import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'
import { ProsePage, ProseSection } from '@/components/prose-section'

export const Route = createFileRoute('/privacy')({
  component: PrivacyPage,
})

function PrivacyPage() {
  return (
    <Page title='Privacy'>
      <ProsePage>
        <ProseSection title='What we collect'>
          <ul>
            <li>No accounts, no sign-in, and no forms.</li>
            <li>
              No advertising or cross-site tracking. The only cookie is{' '}
              <code>sidebar_state</code>, which remembers whether you collapsed
              the side menu and is never sent anywhere that uses it.
            </li>
            <li>
              Anonymous, aggregate page-view statistics through Vercel Web
              Analytics, which works without cookies and does not identify
              individual visitors.
            </li>
          </ul>
        </ProseSection>
        <ProseSection title='Server logs and errors'>
          <p>
            The hosting provider, Vercel, keeps standard request logs (such as
            IP address, page requested and time) for operating and protecting
            the service. Server errors are reported to Sentry without personal
            data, so they can be fixed.
          </p>
        </ProseSection>
      </ProsePage>
    </Page>
  )
}
