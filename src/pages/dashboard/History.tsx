import { useState } from "react";
import { Search, Trash2, Calendar, Filter } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/useAuth";
import { supabase } from "@/integrations/supabase/client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { format } from "date-fns";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

export default function History() {
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const { data: predictions, isLoading } = useQuery({
    queryKey: ["predictions-history", user?.id],
    queryFn: async () => {
      if (!user) return [];
      
      const { data, error } = await supabase
        .from("predictions")
        .select("*")
        .eq("user_id", user.id)
        .order("created_at", { ascending: false });

      if (error) throw error;
      return data || [];
    },
    enabled: !!user,
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase.from("predictions").delete().eq("id", id);
      if (error) throw error;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["predictions-history"] });
      queryClient.invalidateQueries({ queryKey: ["predictions-analytics"] });
      queryClient.invalidateQueries({ queryKey: ["user-stats"] });
      toast({ title: "Deleted", description: "Prediction removed from history." });
    },
    onError: () => {
      toast({ variant: "destructive", title: "Error", description: "Failed to delete prediction." });
    },
  });

  const filteredPredictions = predictions?.filter((p) =>
    p.material_name.toLowerCase().includes(search.toLowerCase())
  ) || [];

  const totalPages = Math.ceil(filteredPredictions.length / itemsPerPage);
  const paginatedPredictions = filteredPredictions.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const getSustainabilityBadge = (score: number) => {
    if (score >= 70) return <Badge className="bg-success text-success-foreground">High</Badge>;
    if (score >= 40) return <Badge className="bg-warning text-warning-foreground">Medium</Badge>;
    return <Badge variant="destructive">Low</Badge>;
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-display font-bold">Prediction History</h2>
        <p className="text-muted-foreground mt-1">
          View and manage your past packaging analyses
        </p>
      </div>

      <Card className="eco-shadow">
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <CardTitle>All Predictions</CardTitle>
              <CardDescription>
                {filteredPredictions.length} total records
              </CardDescription>
            </div>
            <div className="relative w-full sm:w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by material..."
                className="pl-10"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setCurrentPage(1);
                }}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="h-48 flex items-center justify-center">
              <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
          ) : paginatedPredictions.length > 0 ? (
            <>
              <div className="rounded-lg border overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Material</TableHead>
                      <TableHead className="hidden md:table-cell">Tensile</TableHead>
                      <TableHead className="hidden md:table-cell">Weight</TableHead>
                      <TableHead className="hidden lg:table-cell">CO₂</TableHead>
                      <TableHead className="hidden lg:table-cell">Cost</TableHead>
                      <TableHead>Sustainability</TableHead>
                      <TableHead className="w-12"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {paginatedPredictions.map((prediction) => (
                      <TableRow key={prediction.id}>
                        <TableCell className="font-medium">
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-muted-foreground hidden sm:block" />
                            <span className="text-sm">
                              {format(new Date(prediction.created_at), "MMM d, yyyy")}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className="font-medium text-primary">{prediction.material_name}</span>
                        </TableCell>
                        <TableCell className="hidden md:table-cell">
                          {prediction.tensile_strength} MPa
                        </TableCell>
                        <TableCell className="hidden md:table-cell">
                          {prediction.weight_capacity} kg
                        </TableCell>
                        <TableCell className="hidden lg:table-cell">
                          {prediction.co2_emission_score}
                        </TableCell>
                        <TableCell className="hidden lg:table-cell">
                          {prediction.cost_score}
                        </TableCell>
                        <TableCell>
                          {getSustainabilityBadge(Number(prediction.sustainability_score))}
                        </TableCell>
                        <TableCell>
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive">
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Delete prediction?</AlertDialogTitle>
                                <AlertDialogDescription>
                                  This will permanently remove this prediction from your history.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                  onClick={() => deleteMutation.mutate(prediction.id)}
                                >
                                  Delete
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-muted-foreground">
                    Page {currentPage} of {totalPages}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="h-48 flex flex-col items-center justify-center text-muted-foreground">
              <Filter className="h-12 w-12 mb-3 opacity-50" />
              <p>No predictions found</p>
              <p className="text-sm">
                {search ? "Try a different search term" : "Make your first prediction on the Home page"}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
