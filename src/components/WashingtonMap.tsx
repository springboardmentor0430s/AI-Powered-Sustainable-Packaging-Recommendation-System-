import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { supabase } from '@/integrations/supabase/client';

const WashingtonMap = () => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const fetchToken = async () => {
      const { data } = await supabase.functions.invoke('get-mapbox-token');
      if (data?.token) {
        setToken(data.token);
      }
    };
    fetchToken();
  }, []);

  useEffect(() => {
    if (!mapContainer.current || !token) return;

    mapboxgl.accessToken = token;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v11',
      center: [-77.0369, 38.9072], // Washington DC coordinates
      zoom: 11,
      pitch: 45,
    });

    // Add navigation controls
    map.current.addControl(
      new mapboxgl.NavigationControl({
        visualizePitch: true,
      }),
      'top-right'
    );

    // Add marker for Washington DC
    new mapboxgl.Marker({ color: '#22c55e' })
      .setLngLat([-77.0369, 38.9072])
      .setPopup(new mapboxgl.Popup().setHTML('<h3 class="font-bold">EcoPackAI HQ</h3><p>Washington, DC</p>'))
      .addTo(map.current);

    // Cleanup
    return () => {
      map.current?.remove();
    };
  }, [token]);

  if (!token) {
    return (
      <div className="w-full h-64 rounded-xl bg-muted flex items-center justify-center">
        <p className="text-muted-foreground">Loading map...</p>
      </div>
    );
  }

  return (
    <div className="relative w-full h-64 rounded-xl overflow-hidden eco-shadow">
      <div ref={mapContainer} className="absolute inset-0" />
    </div>
  );
};

export default WashingtonMap;
