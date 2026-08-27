import { BuyersDirectory, ContractsRepository, DealsBoard, PropertyDirectory, SearchWorkspace, SellersCRM, SettingsWorkspace } from "@/components/WorkspaceScreens";
import { notFound } from "next/navigation";

export default async function WorkspacePage({ params }: { params: Promise<{ workspace: string }> }) {
  const { workspace } = await params;
  const screens: Record<string, React.ReactNode> = { search: <SearchWorkspace />, properties: <PropertyDirectory />, deals: <DealsBoard />, sellers: <SellersCRM />, buyers: <BuyersDirectory />, contracts: <ContractsRepository />, settings: <SettingsWorkspace /> };
  return screens[workspace] ?? notFound();
}
