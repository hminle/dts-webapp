import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'
import { ProsePage, ProseSection } from '@/components/prose-section'

export const Route = createFileRoute('/terms')({
  component: TermsPage,
})

function TermsPage() {
  return (
    <Page title='Terms of use'>
      <ProsePage>
        <ProseSection title='Informational only'>
          <p>
            DTS Analysis presents public U.S. Treasury data for information and
            education. Nothing on this site is financial, investment, tax or
            legal advice, and it should not be the basis for any financial
            decision.
          </p>
        </ProseSection>
        <ProseSection title='The data'>
          <p>
            The figures come from the Daily Treasury Statement published by the
            U.S. Department of the Treasury, which is in the public domain. This
            site is not affiliated with or endorsed by the Treasury. See the
            Methodology page for how the figures are calculated.
          </p>
        </ProseSection>
        <ProseSection title='No warranty'>
          <p>
            The site is provided as is. The data may be late, incomplete or
            wrong, whether in the Treasury&apos;s source or in this site&apos;s
            processing, and the site may be unavailable at times. To the extent
            the law allows, the operator is not liable for any loss arising from
            its use.
          </p>
        </ProseSection>
        <ProseSection title='Fair use'>
          <p>
            Please don&apos;t overload the service. Automated requests are rate
            limited per IP address.
          </p>
        </ProseSection>
      </ProsePage>
    </Page>
  )
}
