import { DealWorkspaceLive } from "@/components/DealWorkspaceLive";

export default async function DealPage({ params }: { params: Promise<{ dealId: string }> }) {
  const { dealId } = await params;
  return <DealWorkspaceLive dealId={dealId} />;
}
