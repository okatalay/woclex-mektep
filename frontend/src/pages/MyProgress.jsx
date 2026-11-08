import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Card, ErrorNote, PageHeader, PageLoader } from '../components/ui.jsx'
import TrackingSummary from '../components/TrackingSummary.jsx'
import CurriculumChart from '../components/CurriculumChart.jsx'
import PageLogSection from '../components/PageLogSection.jsx'

export default function MyProgress() {
  const { data: summary, loading, error } = useLoad(() => api.get('/me/tracking-summary'), [])

  if (loading) return <PageLoader />
  if (error) return <ErrorNote error={error} />

  return (
    <>
      <PageHeader title="Gelişimim" subtitle="Yoklama, ezber, tecvid ve sayfa takibinin özeti." />

      <Card>
        <h3>Genel bakış</h3>
        <TrackingSummary summary={summary} />
      </Card>

      <PageLogSection />

      <h3>Ezber çizelgesi</h3>
      <CurriculumChart endpoint="/me/curriculum?kind=ezber" />

      <h3>Cüz &amp; tecvid çizelgesi</h3>
      <CurriculumChart endpoint="/me/curriculum?kind=tecvid" />
    </>
  )
}
