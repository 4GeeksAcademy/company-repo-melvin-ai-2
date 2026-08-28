import { BackofficeShell } from "@/components/BackofficeShell";
import { ChangePasswordForm } from "@repo/auth";

export default function ChangePasswordPage() {
  return (
    <BackofficeShell>
      <ChangePasswordForm />
    </BackofficeShell>
  );
}
