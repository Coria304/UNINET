import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { authApi, type LoginPayload, type MFAVerifyPayload } from "@/lib/auth";
import { useAuthStore } from "@/stores/authStore";

/**
 * Hidrata el usuario desde /auth/me al cargar la app si hay token guardado.
 * Si el token está expirado o revocado, el interceptor de axios limpia la sesión.
 */
export function useHydrateSession() {
  const token = useAuthStore((s) => s.token);
  const setUsuario = useAuthStore((s) => s.setUsuario);

  const query = useQuery({
    queryKey: ["auth", "me"],
    queryFn: authApi.me,
    enabled: Boolean(token),
    staleTime: 60_000,
  });

  useEffect(() => {
    if (query.data) setUsuario(query.data);
  }, [query.data, setUsuario]);

  return query;
}

export function useLogin() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const setPendingMfa = useAuthStore((s) => s.setPendingMfa);

  return useMutation({
    mutationFn: (payload: LoginPayload) => authApi.login(payload),
    onSuccess: (data, variables) => {
      if (data.mfa_required) {
        setPendingMfa({
          challengeId: data.challenge_id,
          correo: variables.correo,
          expiresAt: Date.now() + data.expires_in * 1000,
          devCode: data.dev_code,
        });
        navigate("/verify-mfa");
        return;
      }
      login(data.access_token, data.usuario);
      navigate("/");
    },
  });
}

export function useVerifyMfa() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const setPendingMfa = useAuthStore((s) => s.setPendingMfa);

  return useMutation({
    mutationFn: (payload: MFAVerifyPayload) => authApi.verifyMfa(payload),
    onSuccess: (data) => {
      login(data.access_token, data.usuario);
      setPendingMfa(null);
      navigate("/");
    },
  });
}

export function useLogout() {
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);

  return useMutation({
    mutationFn: authApi.logout,
    onSettled: () => {
      logout();
      navigate("/login");
    },
  });
}
