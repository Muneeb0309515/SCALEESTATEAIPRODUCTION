import { BuyersDirectory, ContractsRepository, DealsBoard, PropertyDirectory, SearchWorkspace, SellersCRM, SettingsWorkspace } from "@/components/WorkspaceScreens";
import { StandaloneWorkflowDetails } from "@/components/StandaloneWorkflowDetails";
import { notFound } from "next/navigation";

export default async function WorkspacePage({ params }: { params: Promise<{ workspace: string }> }) {
  const { workspace } = await params;
  const screens: Record<string, React.ReactNode> = { search: <SearchWorkspace />, properties: <PropertyDirectory />, deals: <DealsBoard />, sellers: <SellersCRM />, buyers: <BuyersDirectory />, contracts: <ContractsRepository />, settings: <SettingsWorkspace /> };
  if (!screens[workspace]) return notFound();
  return <>{screens[workspace]}<StandaloneWorkflowDetails mode={workspace as "search" | "properties" | "deals" | "sellers" | "buyers" | "contracts" | "settings"} /></>;
}
