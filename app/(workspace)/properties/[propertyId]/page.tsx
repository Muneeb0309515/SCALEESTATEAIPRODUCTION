import { PropertyIntelligence } from "@/components/WorkspaceScreens";

export default async function PropertyPage({ params }: { params: Promise<{ propertyId: string }> }) {
  const { propertyId } = await params;
  return <PropertyIntelligence propertyId={propertyId} />;
}
