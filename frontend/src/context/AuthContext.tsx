import { createContext, useEffect, useState, type ReactNode } from "react";
import { loginRequest, meRequest, registerRequest, type LoginPayload, type RegisterPayload, type User } from "../services/authService";

type AuthContextValue = {
  user: User | null;
  isAuthenticated: boolean;
  isBootstrapping: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
};

export const AuthContext = createContext<AuthContextValue | null>(null);

type AuthProviderProps = {
  children: ReactNode;
};

const TOKEN_KEY = "mediassist_token";

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  useEffect(() => {
    const bootstrapAuth = async () => {
      const token = localStorage.getItem(TOKEN_KEY);
      if (!token) {
        setIsBootstrapping(false);
        return;
      }

      try {
        const currentUser = await meRequest();
        setUser(currentUser);
      } catch {
        localStorage.removeItem(TOKEN_KEY);
      } finally {
        setIsBootstrapping(false);
      }
    };

    void bootstrapAuth();
  }, []);

  const login = async (payload: LoginPayload) => {
    const token = await loginRequest(payload);
    localStorage.setItem(TOKEN_KEY, token.access_token);
    const currentUser = await meRequest();
    setUser(currentUser);
  };

  const register = async (payload: RegisterPayload) => {
    await registerRequest(payload);
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: Boolean(user),
        isBootstrapping,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
