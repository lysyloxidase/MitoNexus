import { ReportOverviewPage } from "@/components/report/ReportOverviewPage";

type ReportPageProps = {
  params: Promise<{
    reportId: string;
  }>;
};

export default async function ReportPage({ params }: ReportPageProps) {
  const { reportId } = await params;
  return <ReportOverviewPage reportId={reportId} />;
}
