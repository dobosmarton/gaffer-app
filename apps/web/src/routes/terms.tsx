import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";

export const Route = createFileRoute("/terms")({
  component: TermsOfService,
});

function TermsOfService() {
  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-3xl px-4 py-12">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-8"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to home
        </Link>

        <h1 className="text-4xl font-bold text-foreground mb-2">Terms of Service</h1>
        <p className="text-muted-foreground mb-8">Last updated: January 29, 2026</p>

        <div className="prose prose-neutral dark:prose-invert max-w-none">
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">1. Acceptance of Terms</h2>
            <p className="text-muted-foreground mb-4">
              By accessing or using Gaffer ("the Service"), available at meeting-gaffer.com, you
              agree to be bound by these Terms of Service ("Terms"). If you do not agree to these
              Terms, you may not use the Service.
            </p>
            <p className="text-muted-foreground">
              We reserve the right to modify these Terms at any time. Your continued use of the
              Service following any changes constitutes acceptance of the new Terms.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              2. Description of Service
            </h2>
            <p className="text-muted-foreground mb-4">
              Gaffer is a web application that generates AI-powered motivational speeches based on
              your upcoming calendar meetings. The Service:
            </p>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>
                Connects to your Google Calendar (with your permission) to read meeting information
              </li>
              <li>Uses artificial intelligence to generate personalized motivational speeches</li>
              <li>Converts speeches to audio using text-to-speech technology</li>
              <li>Allows you to play and manage your generated speeches</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">3. Account Registration</h2>
            <p className="text-muted-foreground mb-4">
              To use Gaffer, you must sign in using your Google account. By signing in, you:
            </p>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>Confirm that you are at least 13 years of age</li>
              <li>Agree to provide accurate and complete information</li>
              <li>Are responsible for maintaining the security of your account</li>
              <li>Accept responsibility for all activities that occur under your account</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              4. Google Calendar Access
            </h2>
            <p className="text-muted-foreground mb-4">
              Gaffer requires read-only access to your Google Calendar to function. By granting this
              access, you:
            </p>
            <ul className="list-disc list-inside text-muted-foreground mb-4 space-y-1">
              <li>
                Authorize us to read your calendar events for the purpose of generating speeches
              </li>
              <li>Understand that we do not modify, create, or delete any calendar events</li>
              <li>
                Can revoke this access at any time through the app or your Google account settings
              </li>
            </ul>
            <p className="text-muted-foreground">
              Our use of Google Calendar data is governed by our{" "}
              <Link to="/privacy" className="text-amber-500 hover:underline">
                Privacy Policy
              </Link>{" "}
              and complies with Google's API Services User Data Policy.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">5. Acceptable Use</h2>
            <p className="text-muted-foreground mb-4">You agree not to:</p>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>Use the Service for any illegal or unauthorized purpose</li>
              <li>Attempt to gain unauthorized access to the Service or its systems</li>
              <li>Interfere with or disrupt the Service or servers</li>
              <li>Use automated means to access the Service without permission</li>
              <li>Reverse engineer or attempt to extract the source code of the Service</li>
              <li>
                Use the Service to generate content that is harmful, threatening, or harassing
              </li>
              <li>Resell, redistribute, or sublicense the Service without permission</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">6. AI-Generated Content</h2>
            <p className="text-muted-foreground mb-4">
              The motivational speeches generated by Gaffer are created using artificial
              intelligence. You acknowledge that:
            </p>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>
                AI-generated content may occasionally be inaccurate, inappropriate, or unexpected
              </li>
              <li>The speeches are intended for entertainment and motivation purposes only</li>
              <li>
                We do not guarantee the suitability of generated content for any specific purpose
              </li>
              <li>You are responsible for reviewing content before sharing it with others</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              7. Intellectual Property
            </h2>
            <p className="text-muted-foreground mb-4">
              <strong>Our Content:</strong> The Service, including its design, features, and
              underlying technology, is owned by Gaffer and protected by intellectual property laws.
            </p>
            <p className="text-muted-foreground">
              <strong>Your Content:</strong> You retain ownership of your calendar data. The
              speeches generated for you are provided for your personal use. You may use, share, or
              modify your generated speeches as you wish.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">8. Service Availability</h2>
            <p className="text-muted-foreground mb-4">
              We strive to maintain high availability, but:
            </p>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>The Service is provided "as is" without guarantees of uptime</li>
              <li>We may modify, suspend, or discontinue the Service at any time</li>
              <li>We are not liable for any downtime or service interruptions</li>
              <li>Third-party service outages (Google, AI providers) may affect functionality</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">9. Usage Limits</h2>
            <p className="text-muted-foreground">
              We may impose limits on speech generation to ensure fair usage and service quality.
              Current limits, if any, are displayed within the application. We reserve the right to
              modify these limits at any time.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              10. Disclaimer of Warranties
            </h2>
            <p className="text-muted-foreground">
              THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND,
              EXPRESS OR IMPLIED. WE DISCLAIM ALL WARRANTIES INCLUDING, BUT NOT LIMITED TO, IMPLIED
              WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
              WE DO NOT WARRANT THAT THE SERVICE WILL BE UNINTERRUPTED, SECURE, OR ERROR-FREE.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              11. Limitation of Liability
            </h2>
            <p className="text-muted-foreground">
              TO THE MAXIMUM EXTENT PERMITTED BY LAW, GAFFER SHALL NOT BE LIABLE FOR ANY INDIRECT,
              INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING LOSS OF PROFITS,
              DATA, OR GOODWILL, ARISING OUT OF OR RELATED TO YOUR USE OF THE SERVICE, REGARDLESS OF
              WHETHER SUCH DAMAGES WERE FORESEEABLE OR WHETHER WE WERE ADVISED OF THE POSSIBILITY OF
              SUCH DAMAGES.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">12. Indemnification</h2>
            <p className="text-muted-foreground">
              You agree to indemnify and hold harmless Gaffer and its operators from any claims,
              damages, losses, or expenses (including reasonable legal fees) arising from your use
              of the Service or violation of these Terms.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">13. Termination</h2>
            <p className="text-muted-foreground mb-4">
              We may terminate or suspend your access to the Service at any time, with or without
              cause, with or without notice. You may stop using the Service at any time by:
            </p>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>Disconnecting your Google Calendar from the app</li>
              <li>Revoking Gaffer's access in your Google account settings</li>
              <li>Requesting account deletion by contacting us</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">14. Governing Law</h2>
            <p className="text-muted-foreground">
              These Terms shall be governed by and construed in accordance with the laws of Hungary,
              without regard to its conflict of law provisions.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">15. Contact</h2>
            <p className="text-muted-foreground">
              If you have any questions about these Terms, please contact us at:{" "}
              <a
                href="mailto:support@meeting-gaffer.com"
                className="text-amber-500 hover:underline"
              >
                support@meeting-gaffer.com
              </a>
            </p>
          </section>
        </div>

        <div className="mt-12 pt-8 border-t border-border">
          <Link
            to="/"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            &larr; Back to Gaffer
          </Link>
        </div>
      </div>
    </div>
  );
}
