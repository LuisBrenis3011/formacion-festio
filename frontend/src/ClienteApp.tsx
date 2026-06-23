import { useState, useEffect, useRef } from "react";
import { AppHeader } from "./components/app-header";
import { useAuth } from "./hooks/useAuth";
import { useChat } from "./hooks/use-chat";
import { useBookingDetail } from "./hooks/use-booking-detail";
import { useExtras } from "./hooks/use-extras";
import { usePaymentFlow } from "./hooks/use-payment-flow";
import { ChatScreen } from "./screens/chat-screen";
import { DetailScreen } from "./screens/detail-screen";
import { SuccessScreen } from "./screens/success-screen";
import { PaymentModal } from "./screens/payment-modal";
import type { Screen } from "./types";
import type { ContinueToPaymentParams } from "./hooks/use-payment-flow";

export function ClienteApp() {
  const [screen, setScreen] = useState<Screen>("chat");
  const { isAuthenticated, user, openAuthModal } = useAuth();

  const chat = useChat();
  const booking = useBookingDetail(() => setScreen("detail"));
  const extras = useExtras(booking.selectedProvider, booking.providerServices);
  const payment = usePaymentFlow({ onSuccess: () => setScreen("success") });

  // When user wasn't authenticated and we opened the auth modal,
  // store the pending params so we can resume after auth succeeds.
  const pendingPaymentParams = useRef<ContinueToPaymentParams | null>(null);

  // Watch for authentication: if we had pending payment params, proceed.
  useEffect(() => {
    if (isAuthenticated && pendingPaymentParams.current) {
      const params = pendingPaymentParams.current;
      pendingPaymentParams.current = null;
      payment.continueToPayment(params);
    }
  }, [isAuthenticated]);

  const handleContinueToPayment = (params: ContinueToPaymentParams) => {
    if (!isAuthenticated) {
      // Save params and open the real auth modal
      pendingPaymentParams.current = params;
      openAuthModal("login");
      return;
    }
    payment.continueToPayment(params);
  };

  return (
    <div className={`app-shell screen-${screen}`}>
      <AppHeader onLogoClick={() => setScreen("chat")} />

      {screen === "chat" ? (
        <ChatScreen
          messages={chat.messages}
          isPending={chat.isPending}
          handleSend={chat.handleSend}
          messagesEndRef={chat.messagesEndRef}
          onSelectProvider={booking.openPackage}
          loadingDetail={booking.loadingDetail}
          latestRecommendation={chat.latestRecommendation}
          onGoHome={chat.resetChat}
          filters={chat.filters}
          setFilters={chat.setFilters}
        />
      ) : screen === "detail" && booking.selectedProvider ? (
        <DetailScreen
          provider={booking.selectedProvider}
          eventDraft={booking.eventDraft}
          setEventDraft={booking.setEventDraft}
          extras={extras.extras}
          extraQuantities={extras.extraQuantities}
          updateExtra={extras.updateExtra}
          extraTotal={extras.extraTotal}
          total={extras.total}
          advance={extras.advance}
          balance={extras.balance}
          packageDurationHours={extras.packageDurationHours}
          selectedExtras={extras.selectedExtras}
          eventType={chat.latestRecommendation?.estado_conversacion?.tipo_evento}
          error={booking.error || payment.error}
          loadingPayment={payment.loadingPayment}
          onBack={() => setScreen("chat")}
          onContinue={handleContinueToPayment}
        />
      ) : screen === "success" && payment.confirmation ? (
        <SuccessScreen
          confirmation={payment.confirmation}
          preReserva={payment.preReserva}
          provider={booking.selectedProvider}
          eventDraft={booking.eventDraft}
          onBack={() => setScreen("chat")}
        />
      ) : null}

      {payment.paymentOpen && payment.preReserva && user && (
        <PaymentModal
          preReserva={payment.preReserva}
          user={user}
          loadingPayment={payment.loadingPayment}
          error={payment.error}
          onSubmit={(e, metodoPago) =>
            payment.submitPayment(e, booking.eventDraft.direccion, metodoPago)
          }
          onClose={() => payment.setPaymentOpen(false)}
        />
      )}
    </div>
  );
}

