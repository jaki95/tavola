import { useEffect, useState } from "react";

import { getHealth } from "./api/health";
import type { BackendStatus } from "./components/BackendStatusPanel";
import { HomePage } from "./pages/HomePage";

type AppProps = {
  backendStatus?: BackendStatus;
};

export function App({ backendStatus: providedBackendStatus }: AppProps) {
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({
    state: "loading"
  });

  useEffect(() => {
    if (providedBackendStatus) {
      return;
    }

    let isCurrent = true;

    async function refreshBackendStatus() {
      const result = await getHealth();

      if (!isCurrent) {
        return;
      }

      if (result.ok) {
        setBackendStatus({
          state: "success",
          serviceName: result.data.service
        });
        return;
      }

      setBackendStatus({
        state: "error",
        message: result.error.message
      });
    }

    void refreshBackendStatus();

    return () => {
      isCurrent = false;
    };
  }, [providedBackendStatus]);

  return <HomePage backendStatus={providedBackendStatus ?? backendStatus} />;
}
