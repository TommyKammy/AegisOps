import { Box, Button, CircularProgress, Stack, Typography } from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import type { AuthProvider } from "react-admin";
import { OperatorShell } from "./OperatorShell";
import {
  AuthAccessError,
  createOperatorAuthProvider,
} from "../auth/authProvider";
import {
  OperatorUiConfig,
  createOperatorUiConfig,
} from "../auth/config";
import {
  Redirector,
  windowLocationRedirector,
} from "../auth/navigation";
import {
  SessionStore,
  createSessionStore,
} from "../auth/session";

export interface OperatorAppDependencies {
  authProvider: AuthProvider;
  config: OperatorUiConfig;
  sessionStore: SessionStore;
}

interface OperatorDependencyOverrides {
  config?: Partial<OperatorUiConfig>;
  fetchFn?: typeof fetch;
  redirector?: Redirector;
}

export function createDefaultDependencies(
  overrides: OperatorDependencyOverrides = {},
): OperatorAppDependencies {
  const config = createOperatorUiConfig(overrides.config);
  const sessionStore = createSessionStore({
    config,
    fetchFn: overrides.fetchFn,
  });

  const authProvider = createOperatorAuthProvider({
    config,
    sessionStore,
    fetchFn: overrides.fetchFn,
    redirector: overrides.redirector ?? windowLocationRedirector,
  });

  return {
    authProvider,
    config,
    sessionStore,
  };
}

function LoginPage({
  authProvider,
  config,
}: {
  authProvider: AuthProvider;
  config: OperatorUiConfig;
}) {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const returnTo = params.get("returnTo") ?? config.basePath;

  return (
    <Stack
      spacing={2}
      sx={{
        minHeight: "100vh",
        alignItems: "center",
        justifyContent: "center",
        px: 3,
      }}
    >
      <Typography component="h1" variant="h3">
        Operator Sign-In
      </Typography>
      <Typography maxWidth={520} textAlign="center" variant="body1">
        Approved OIDC sign-in is required before the operator shell can render.
        The browser does not accept placeholder credentials or client-owned
        identity claims.
      </Typography>
      <Typography color="text.secondary" variant="body2">
        Return path: {returnTo}
      </Typography>
      <Button
        onClick={() => {
          void authProvider.login({ returnTo });
        }}
        size="large"
        variant="contained"
      >
        Continue With Reviewed OIDC
      </Button>
    </Stack>
  );
}

function ForbiddenPage({
  authProvider,
}: {
  authProvider: AuthProvider;
}) {
  return (
    <Stack
      spacing={2}
      sx={{
        minHeight: "100vh",
        alignItems: "center",
        justifyContent: "center",
        px: 3,
      }}
    >
      <Typography component="h1" variant="h3">
        Access denied
      </Typography>
      <Typography maxWidth={560} textAlign="center" variant="body1">
        The current session is authenticated but does not carry one of the
        reviewed operator roles required for this shell.
      </Typography>
      <Button
        onClick={() => {
          void authProvider.logout({});
        }}
        variant="outlined"
      >
        End Session
      </Button>
    </Stack>
  );
}

function InvalidSessionPage({
  authProvider,
}: {
  authProvider: AuthProvider;
}) {
  return (
    <Stack
      spacing={2}
      sx={{
        minHeight: "100vh",
        alignItems: "center",
        justifyContent: "center",
        px: 3,
      }}
    >
      <Typography component="h1" variant="h3">
        Session verification failed
      </Typography>
      <Typography maxWidth={560} textAlign="center" variant="body1">
        The reviewed backend session is missing required operator claims or
        returned an unexpected auth response. The operator shell remains
        blocked until a reviewed session is re-established.
      </Typography>
      <Button
        onClick={() => {
          void authProvider.logout({});
        }}
        variant="outlined"
      >
        Clear Session
      </Button>
    </Stack>
  );
}

function ProtectedOperatorRoute({
  authProvider,
  config,
  sessionStore,
}: OperatorAppDependencies) {
  const location = useLocation();
  const [status, setStatus] = useState<
    "loading" | "authorized" | "forbidden" | "invalid_session" | "unauthenticated"
  >("loading");

  useEffect(() => {
    let active = true;

    void sessionStore
      .getSession({ force: true })
      .then(() => {
        if (active) {
          setStatus("authorized");
        }
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }

        if (error instanceof AuthAccessError) {
          if (error.code === "forbidden") {
            setStatus("forbidden");
            return;
          }

          if (error.code === "invalid_session") {
            setStatus("invalid_session");
            return;
          }

          setStatus("unauthenticated");
          return;
        }

        setStatus("unauthenticated");
      });

    return () => {
      active = false;
    };
  }, [sessionStore]);

  const loginHref = useMemo(() => {
    const returnTo =
      location.pathname + location.search + location.hash || config.basePath;
    return `${config.basePath}/login?returnTo=${encodeURIComponent(returnTo)}`;
  }, [config.basePath, location.hash, location.pathname, location.search]);

  if (status === "loading") {
    return (
      <Box
        sx={{
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
        }}
      >
        <CircularProgress aria-label="Checking operator session" />
      </Box>
    );
  }

  if (status === "forbidden") {
    return <Navigate replace to={`${config.basePath}/forbidden`} />;
  }

  if (status === "invalid_session") {
    return <Navigate replace to={`${config.basePath}/session-invalid`} />;
  }

  if (status === "unauthenticated") {
    return <Navigate replace to={loginHref} />;
  }

  return <OperatorShell authProvider={authProvider} />;
}

export function OperatorRoutes({
  dependencies,
}: {
  dependencies: OperatorAppDependencies;
}) {
  const { authProvider, config, sessionStore } = dependencies;

  return (
    <Routes>
      <Route
        element={<LoginPage authProvider={authProvider} config={config} />}
        path={`${config.basePath}/login`}
      />
      <Route
        element={<ForbiddenPage authProvider={authProvider} />}
        path={`${config.basePath}/forbidden`}
      />
      <Route
        element={<InvalidSessionPage authProvider={authProvider} />}
        path={`${config.basePath}/session-invalid`}
      />
      <Route
        element={
          <ProtectedOperatorRoute
            authProvider={authProvider}
            config={config}
            sessionStore={sessionStore}
          />
        }
        path={`${config.basePath}/*`}
      />
      <Route element={<Navigate replace to={config.basePath} />} path="*" />
    </Routes>
  );
}
