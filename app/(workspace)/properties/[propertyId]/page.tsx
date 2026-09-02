import { PropertyIntelligenceLive } from "@/components/PropertyIntelligenceLive";

export default async function PropertyPage({ params, searchParams }: { params: Promise<{ propertyId: string }>; searchParams: Promise<{ address?: string }> }) {
  const { propertyId } = await params;
  const { address } = await searchParams;
  return <PropertyIntelligenceLive propertyId={propertyId} address={address} />;
}
