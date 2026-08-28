import { BackofficeShell } from "@/components/BackofficeShell";
import { ProfileForm } from "@repo/auth";

export default function ProfilePage() {
  return (
    <BackofficeShell>
      <ProfileForm />
    </BackofficeShell>
  );
}
