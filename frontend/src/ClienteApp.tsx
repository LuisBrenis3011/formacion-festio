import { useState } from "react";
import { AppHeader } from "./components/app-header";
import { useChat } from "./hooks/use-chat";
import { useBookingDetail } from "./hooks/use-booking-detail";
import { useExtras } from "./hooks/use-extras";
import { usePaymentFlow } from "./hooks/use-payment-flow";
import { ChatScreen } from "./screens/chat-screen";
import { DetailScreen } from "./screens/detail-screen";
import { SuccessScreen } from "./screens/success-screen";
import { PaymentModal } from "./screens/payment-modal";
import type { Screen } from "./types";

export function ClienteApp() {
  const [screen, setScreen] = useState<Screen>("chat");

  const chat = useChat();
  const booking = useBookingDetail(() => setScreen("detail"));
  const extras = useExtras(booking.selectedProvider, booking.providerServices);
  const payment = usePaymentFlow({ onSuccess: () => setScreen("success") });

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
          onContinue={payment.continueToPayment}
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

      {payment.paymentOpen && payment.preReserva && (
        <PaymentModal
          preReserva={payment.preReserva}
          authTab={payment.authTab}
          setAuthTab={payment.setAuthTab}
          registerDraft={payment.registerDraft}
          setRegisterDraft={payment.setRegisterDraft}
          loginDraft={payment.loginDraft}
          setLoginDraft={payment.setLoginDraft}
          loadingPayment={payment.loadingPayment}
          error={payment.error}
          onSubmit={(e) => payment.submitPayment(e, booking.eventDraft.direccion)}
          onClose={() => payment.setPaymentOpen(false)}
        />
      )}
    </div>
  );
}
