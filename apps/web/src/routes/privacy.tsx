import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";

export const Route = createFileRoute("/privacy")({
  component: PrivacyPolicy,
});

function PrivacyPolicy() {
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

        <h1 className="text-4xl font-bold text-foreground mb-2">Privacy Policy</h1>
        <p className="text-muted-foreground mb-8">Last updated: February 7, 2026</p>

        <div className="prose prose-neutral dark:prose-invert max-w-none">
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">1. Introduction</h2>
            <p className="text-muted-foreground mb-4">
              Gaffer ("we," "our," or "us") is a web application that generates motivational
              speeches for your upcoming meetings. This Privacy Policy explains how we collect, use,
              disclose, and safeguard your information when you use our service at
              meeting-gaffer.com.
            </p>
            <p className="text-muted-foreground">
              By using Gaffer, you agree to the collection and use of information in accordance with
              this policy.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              2. Information We Collect
            </h2>

            <h3 className="text-xl font-medium text-foreground mb-3">2.1 Account Information</h3>
            <p className="text-muted-foreground mb-4">
              When you sign in with Google, we receive and store:
            </p>
            <ul className="list-disc list-inside text-muted-foreground mb-4 space-y-1">
              <li>Your email address</li>
              <li>Your name (as provided by Google)</li>
              <li>Your profile picture URL</li>
            </ul>

            <h3 className="text-xl font-medium text-foreground mb-3">2.2 Google Calendar Data</h3>
            <p className="text-muted-foreground mb-4">
              With your explicit consent, we access your Google Calendar with read-only permissions.
              We collect:
            </p>
            <ul className="list-disc list-inside text-muted-foreground mb-4 space-y-1">
              <li>Meeting titles</li>
              <li>Meeting start and end times</li>
              <li>Meeting descriptions (optional, used to personalize speeches)</li>
              <li>Attendee names (not email addresses)</li>
            </ul>
            <p className="text-muted-foreground mb-4">
              <strong>Important:</strong> We only access calendar events for the purpose of
              generating personalized motivational speeches. We do not store your calendar data
              permanently — it is fetched on-demand and used only during speech generation.
            </p>

            <h3 className="text-xl font-medium text-foreground mb-3">2.3 Generated Content</h3>
            <p className="text-muted-foreground mb-4">
              We store the motivational speeches and audio files we generate for you so you can
              replay them later.
            </p>

            <h3 className="text-xl font-medium text-foreground mb-3">2.4 Usage Data</h3>
            <p className="text-muted-foreground">
              We collect anonymized usage statistics such as the number of speeches generated to
              improve our service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              3. How We Use Your Information
            </h2>
            <p className="text-muted-foreground mb-4">We use the collected information to:</p>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>Authenticate you and maintain your account</li>
              <li>Fetch your upcoming calendar events</li>
              <li>Generate personalized motivational speeches based on your meetings</li>
              <li>Convert text speeches to audio</li>
              <li>Store your generated speeches for later playback</li>
              <li>Improve and optimize our service</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">4. Third-Party Services</h2>
            <p className="text-muted-foreground mb-4">
              We use the following third-party services to provide our functionality:
            </p>

            <h3 className="text-xl font-medium text-foreground mb-3">
              4.1 Google (Authentication & Calendar)
            </h3>
            <p className="text-muted-foreground mb-4">
              We use Google OAuth for authentication and Google Calendar API to access your meeting
              information. Google's privacy policy applies to their processing of your data:{" "}
              <a
                href="https://policies.google.com/privacy"
                target="_blank"
                rel="noopener noreferrer"
                className="text-amber-500 hover:underline"
              >
                https://policies.google.com/privacy
              </a>
            </p>

            <h3 className="text-xl font-medium text-foreground mb-3">
              4.2 Supabase (Database & Authentication)
            </h3>
            <p className="text-muted-foreground mb-4">
              We use Supabase to store your account information, encrypted tokens, and generated
              content. Supabase's privacy policy:{" "}
              <a
                href="https://supabase.com/privacy"
                target="_blank"
                rel="noopener noreferrer"
                className="text-amber-500 hover:underline"
              >
                https://supabase.com/privacy
              </a>
            </p>

            <h3 className="text-xl font-medium text-foreground mb-3">
              4.3 Anthropic (AI Speech Generation)
            </h3>
            <p className="text-muted-foreground mb-4">
              We use Anthropic's Claude AI to generate your motivational speeches. Meeting titles
              and descriptions are sent to Anthropic for speech generation. Anthropic's privacy
              policy:{" "}
              <a
                href="https://www.anthropic.com/privacy"
                target="_blank"
                rel="noopener noreferrer"
                className="text-amber-500 hover:underline"
              >
                https://www.anthropic.com/privacy
              </a>
            </p>

            <h3 className="text-xl font-medium text-foreground mb-3">
              4.4 ElevenLabs (Text-to-Speech)
            </h3>
            <p className="text-muted-foreground mb-4">
              We use ElevenLabs to convert generated speeches into audio. The text of your speeches
              is sent to ElevenLabs for audio generation. ElevenLabs' privacy policy:{" "}
              <a
                href="https://elevenlabs.io/privacy"
                target="_blank"
                rel="noopener noreferrer"
                className="text-amber-500 hover:underline"
              >
                https://elevenlabs.io/privacy
              </a>
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              5. Data Sharing and Disclosure
            </h2>
            <p className="text-muted-foreground mb-4">
              We share, transfer, or disclose Google user data only as described below:
            </p>

            <h3 className="text-xl font-medium text-foreground mb-3">
              5.1 Third-Party Service Providers
            </h3>
            <p className="text-muted-foreground mb-4">
              We share limited Google user data with the following service providers solely to
              provide the Gaffer service:
            </p>
            <ul className="list-disc list-inside text-muted-foreground mb-4 space-y-2">
              <li>
                <strong>Anthropic (Claude AI):</strong> We share meeting titles and descriptions
                from your Google Calendar to generate personalized motivational speeches. No other
                calendar data (such as attendee emails or calendar IDs) is shared with Anthropic.
              </li>
              <li>
                <strong>ElevenLabs:</strong> We share the generated speech text (which may
                reference meeting information) to convert it to audio. ElevenLabs does not receive
                direct access to your Google Calendar data.
              </li>
              <li>
                <strong>Supabase:</strong> We store your Google account email, name, and profile
                picture URL, as well as encrypted OAuth tokens, in our Supabase database to
                maintain your account.
              </li>
            </ul>

            <h3 className="text-xl font-medium text-foreground mb-3">5.2 What We Do NOT Do</h3>
            <p className="text-muted-foreground mb-4">We do NOT:</p>
            <ul className="list-disc list-inside text-muted-foreground mb-4 space-y-1">
              <li>Sell your Google user data to any third party</li>
              <li>Share your Google user data for advertising purposes</li>
              <li>
                Transfer your Google user data to any parties other than those listed above
              </li>
              <li>
                Use your Google user data for any purpose other than providing the Gaffer service
              </li>
            </ul>

            <h3 className="text-xl font-medium text-foreground mb-3">5.3 Legal Disclosure</h3>
            <p className="text-muted-foreground">
              We may disclose your information if required by law, such as in response to a valid
              legal process (e.g., subpoena, court order, or government request), or to protect
              the rights, property, or safety of Gaffer, our users, or others.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">6. Data Security</h2>
            <p className="text-muted-foreground mb-4">
              We implement appropriate security measures to protect your information:
            </p>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>All data is transmitted over HTTPS (TLS encryption)</li>
              <li>
                Google OAuth refresh tokens are encrypted at rest using industry-standard encryption
                (Fernet/AES)
              </li>
              <li>Database access is protected by row-level security policies</li>
              <li>
                We do not store your Google password — authentication is handled entirely by Google
              </li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">7. Data Retention</h2>
            <p className="text-muted-foreground mb-4">
              We retain your data for as long as your account is active. Specifically:
            </p>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>Account information: Retained until you delete your account</li>
              <li>
                Google OAuth tokens: Retained until you disconnect Google or delete your account
              </li>
              <li>
                Generated speeches and audio: Retained until you delete them or delete your account
              </li>
              <li>Calendar data: Not stored permanently; fetched on-demand only</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">8. Your Rights</h2>
            <p className="text-muted-foreground mb-4">You have the right to:</p>
            <ul className="list-disc list-inside text-muted-foreground mb-4 space-y-1">
              <li>
                <strong>Access:</strong> Request a copy of the personal data we hold about you
              </li>
              <li>
                <strong>Rectification:</strong> Request correction of inaccurate personal data
              </li>
              <li>
                <strong>Deletion:</strong> Request deletion of your account and all associated data
              </li>
              <li>
                <strong>Revoke access:</strong> Disconnect your Google Calendar at any time through
                the app settings
              </li>
              <li>
                <strong>Portability:</strong> Request your data in a portable format
              </li>
            </ul>
            <p className="text-muted-foreground">
              To exercise any of these rights, please contact us at the email address below.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              9. Google API Services User Data Policy
            </h2>
            <p className="text-muted-foreground mb-4">
              Gaffer's use and transfer of information received from Google APIs adheres to the{" "}
              <a
                href="https://developers.google.com/terms/api-services-user-data-policy"
                target="_blank"
                rel="noopener noreferrer"
                className="text-amber-500 hover:underline"
              >
                Google API Services User Data Policy
              </a>
              , including the Limited Use requirements.
            </p>
            <p className="text-muted-foreground">
              We only use Google Calendar data for the purpose of generating personalized
              motivational speeches. We do not use this data for advertising, do not sell this data
              to third parties, and do not use it for any purpose other than providing the Gaffer
              service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">10. Children's Privacy</h2>
            <p className="text-muted-foreground">
              Gaffer is not intended for use by children under the age of 13. We do not knowingly
              collect personal information from children under 13. If you believe we have collected
              information from a child under 13, please contact us immediately.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              11. Changes to This Policy
            </h2>
            <p className="text-muted-foreground">
              We may update this Privacy Policy from time to time. We will notify you of any changes
              by posting the new Privacy Policy on this page and updating the "Last updated" date.
              Your continued use of the service after any changes constitutes acceptance of the new
              Privacy Policy.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">12. Contact Us</h2>
            <p className="text-muted-foreground">
              If you have any questions about this Privacy Policy or our data practices, please
              contact us at:{" "}
              <a
                href="mailto:privacy@meeting-gaffer.com"
                className="text-amber-500 hover:underline"
              >
                privacy@meeting-gaffer.com
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
