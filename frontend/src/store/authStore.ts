import { create } from "zustand";

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("courtcrm_token"),
  isAuthenticated: !!localStorage.getItem("courtcrm_token"),
  login: (token: string) => {
    localStorage.setItem("courtcrm_token", token);
    set({ token, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem("courtcrm_token");
    set({ token: null, isAuthenticated: false });
  },
}));
