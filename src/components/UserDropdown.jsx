import { useNavigate } from "react-router-dom";

export default function UserDropdown() {
  const navigate = useNavigate();

  return (
    <div className="absolute right-0 mt-2 w-40 bg-white border rounded-lg shadow">
      <button className="block w-full px-4 py-2 hover:bg-gray-100">
        Edit Profile
      </button>
      <button
        className="block w-full px-4 py-2 text-red-600 hover:bg-gray-100"
        onClick={() => navigate("/login")}
      >
        Logout
      </button>
    </div>
  );
}
