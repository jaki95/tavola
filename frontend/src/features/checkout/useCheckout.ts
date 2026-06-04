import { useCallback, useEffect, useRef, useState } from "react";

import { createCheckout, listPickupWindows } from "../../api/checkout";
import type { ApiResult } from "../../api/client";
import type { Basket } from "../../types/basket";
import type {
  CheckoutRequest,
  CheckoutResponse,
  Order,
  PickupWindow
} from "../../types/checkout";

export type CheckoutClient = {
  getPickupWindows: typeof listPickupWindows;
  createCheckout: typeof createCheckout;
};

export type PickupWindowsState =
  | {
      status: "loading";
      pickupWindows: PickupWindow[];
      message: null;
    }
  | {
      status: "success";
      pickupWindows: PickupWindow[];
      message: null;
    }
  | {
      status: "empty";
      pickupWindows: [];
      message: string;
    }
  | {
      status: "error";
      pickupWindows: PickupWindow[];
      message: string;
    };

export type CheckoutSubmissionState =
  | {
      status: "idle";
      message: null;
      order: null;
    }
  | {
      status: "pending";
      message: null;
      order: null;
    }
  | {
      status: "error";
      message: string;
      order: null;
    }
  | {
      status: "success";
      message: null;
      order: Order;
    };

export type CheckoutFormValues = {
  contactName: string;
  contactEmail: string;
  pickupWindowId: string;
};

type UseCheckoutOptions = {
  client?: CheckoutClient;
};

const defaultCheckoutClient: CheckoutClient = {
  getPickupWindows: listPickupWindows,
  createCheckout
};

const idleSubmission: CheckoutSubmissionState = {
  status: "idle",
  message: null,
  order: null
};

export function useCheckout({
  client = defaultCheckoutClient
}: UseCheckoutOptions = {}) {
  const [pickupWindows, setPickupWindows] = useState<PickupWindowsState>({
    status: "loading",
    pickupWindows: [],
    message: null
  });
  const [submission, setSubmission] =
    useState<CheckoutSubmissionState>(idleSubmission);
  const loadRequestId = useRef(0);

  const reloadPickupWindows = useCallback(async () => {
    const requestId = loadRequestId.current + 1;
    loadRequestId.current = requestId;

    setPickupWindows((current) => ({
      status: "loading",
      pickupWindows: current.pickupWindows,
      message: null
    }));

    const result = await client.getPickupWindows();

    if (loadRequestId.current !== requestId) {
      return;
    }

    if (!result.ok) {
      setPickupWindows({
        status: "error",
        pickupWindows: [],
        message: result.error.message
      });
      return;
    }

    if (result.data.pickup_windows.length === 0) {
      setPickupWindows({
        status: "empty",
        pickupWindows: [],
        message: "No pickup windows are available right now."
      });
      return;
    }

    setPickupWindows({
      status: "success",
      pickupWindows: result.data.pickup_windows,
      message: null
    });
  }, [client]);

  useEffect(() => {
    void reloadPickupWindows();
  }, [reloadPickupWindows]);

  const submitCheckout = useCallback(
    async (
      basket: Basket | null,
      values: CheckoutFormValues
    ): Promise<CheckoutResponse | null> => {
      if (!basket) {
        setSubmission({
          status: "error",
          message: "Basket is not ready yet.",
          order: null
        });
        return null;
      }

      if (basket.lines.length === 0) {
        setSubmission({
          status: "error",
          message: "Add at least one deli item before checkout.",
          order: null
        });
        return null;
      }

      setSubmission({
        status: "pending",
        message: null,
        order: null
      });

      const request: CheckoutRequest = {
        basket_id: basket.basket_id,
        contact_name: values.contactName,
        contact_email: values.contactEmail,
        pickup_window_id: values.pickupWindowId
      };
      const result: ApiResult<CheckoutResponse> =
        await client.createCheckout(request);

      if (!result.ok) {
        setSubmission({
          status: "error",
          message: result.error.message,
          order: null
        });
        return null;
      }

      setSubmission({
        status: "success",
        message: null,
        order: result.data.order
      });
      return result.data;
    },
    [client]
  );

  const resetCheckout = useCallback(() => {
    setSubmission(idleSubmission);
  }, []);

  return {
    pickupWindows,
    submission,
    reloadPickupWindows,
    submitCheckout,
    resetCheckout
  };
}
