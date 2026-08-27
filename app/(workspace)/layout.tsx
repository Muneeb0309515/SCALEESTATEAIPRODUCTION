import { WorkspaceShell } from "@/components/WorkspaceShell";

export default function WorkspaceLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <WorkspaceShell>{children}</WorkspaceShell>;
}
