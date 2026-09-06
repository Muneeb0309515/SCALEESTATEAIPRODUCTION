import { DealWorkspace } from "@/components/WorkspaceScreens";

export default async function DealPage({ params }: { params: Promise<{ dealId: string }> }) {
  const { dealId } = await params;
  return <DealWorkspace dealId={dealId} />;
}
