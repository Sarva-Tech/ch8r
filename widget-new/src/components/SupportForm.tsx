import { useState } from 'preact/hooks';
import { createApiClient } from '../services/api';
import { sessionStore } from '../services/session';
import { config } from '../store/signals';
import type { SupportFormData, SupportFormErrors } from '../types/index';

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const EMPTY_FORM: SupportFormData = { name: '', email: '', subject: '', body: '' };
const EMPTY_ERRORS: SupportFormErrors = {};

export function SupportForm() {
  const [form, setForm] = useState<SupportFormData>(EMPTY_FORM);
  const [errors, setErrors] = useState<SupportFormErrors>(EMPTY_ERRORS);
  const [submitted, setSubmitted] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const setField = (field: keyof SupportFormData) => (e: Event) => {
    setForm((prev: SupportFormData) => ({ ...prev, [field]: (e.target as HTMLInputElement | HTMLTextAreaElement).value }));
    setErrors((prev: SupportFormErrors) => ({ ...prev, [field]: undefined }));
  };

  const validate = (): SupportFormErrors => {
    const errs: SupportFormErrors = {};
    if (!form.name.trim()) errs.name = 'Name is required';
    if (!form.email.trim()) {
      errs.email = 'Email is required';
    } else if (!EMAIL_REGEX.test(form.email.trim())) {
      errs.email = 'Please enter a valid email address';
    }
    if (!form.subject.trim()) errs.subject = 'Subject is required';
    if (!form.body.trim()) errs.body = 'Message is required';
    return errs;
  };

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    setApiError(null);

    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }

    setLoading(true);
    const appUuid = config.value?.appUuid ?? '';
    const senderIdentifier = sessionStore.getSenderIdentifier(config.value?.userIdentifier, appUuid);

    const apiClient = createApiClient(
      config.value?.apiBaseUrl ?? window.location.origin,
      config.value?.token ?? '',
    );

    const result = await apiClient.submitSupportForm(appUuid, {
      name: form.name.trim(),
      email: form.email.trim(),
      subject: form.subject.trim(),
      body: form.body.trim(),
      sender_identifier: senderIdentifier,
    });

    setLoading(false);

    if (result.ok) {
      setSubmitted(true);
      setForm(EMPTY_FORM);
      setErrors(EMPTY_ERRORS);
    } else {
      setApiError(result.error);
    }
  };

  if (submitted) {
    return (
      <div class="flex flex-col items-center justify-center h-full px-6 py-8 text-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-12 h-12 text-green-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        <p class="text-sm text-gray-700">Your message has been sent. We'll get back to you soon.</p>
        <button
          onClick={() => setSubmitted(false)}
          class="mt-4 text-sm underline hover:no-underline"
          style={{ color: 'var(--ch8r-accent)' }}
        >
          Send another message
        </button>
      </div>
    );
  }

  return (
    <div class="flex-1 overflow-y-auto px-4 py-4">
      <form onSubmit={handleSubmit} noValidate class="flex flex-col gap-4">
        {apiError && (
          <div class="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-700">
            {apiError}
          </div>
        )}

        {/* Name */}
        <div class="flex flex-col gap-1">
          <label htmlFor="ch8r-name" class="text-sm font-medium text-gray-700">
            Name
          </label>
          <input
            id="ch8r-name"
            type="text"
            value={form.name}
            onInput={setField('name')}
            placeholder="Your name"
            class={`rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 ${
              errors.name ? 'border-red-400 focus:ring-red-300' : 'border-gray-300'
            }`}
          />
          {errors.name && <p class="text-xs text-red-600">{errors.name}</p>}
        </div>

        {/* Email */}
        <div class="flex flex-col gap-1">
          <label htmlFor="ch8r-email" class="text-sm font-medium text-gray-700">
            Email
          </label>
          <input
            id="ch8r-email"
            type="email"
            value={form.email}
            onInput={setField('email')}
            placeholder="you@example.com"
            class={`rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 ${
              errors.email ? 'border-red-400 focus:ring-red-300' : 'border-gray-300'
            }`}
          />
          {errors.email && <p class="text-xs text-red-600">{errors.email}</p>}
        </div>

        {/* Subject */}
        <div class="flex flex-col gap-1">
          <label htmlFor="ch8r-subject" class="text-sm font-medium text-gray-700">
            Subject
          </label>
          <input
            id="ch8r-subject"
            type="text"
            value={form.subject}
            onInput={setField('subject')}
            placeholder="How can we help?"
            class={`rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 ${
              errors.subject ? 'border-red-400 focus:ring-red-300' : 'border-gray-300'
            }`}
          />
          {errors.subject && <p class="text-xs text-red-600">{errors.subject}</p>}
        </div>

        {/* Body */}
        <div class="flex flex-col gap-1">
          <label htmlFor="ch8r-body" class="text-sm font-medium text-gray-700">
            Message
          </label>
          <textarea
            id="ch8r-body"
            value={form.body}
            onInput={setField('body')}
            placeholder="Describe your issue…"
            rows={4}
            class={`rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 resize-none ${
              errors.body ? 'border-red-400 focus:ring-red-300' : 'border-gray-300'
            }`}
          />
          {errors.body && <p class="text-xs text-red-600">{errors.body}</p>}
        </div>

        <button
          type="submit"
          disabled={loading}
          class="w-full rounded-lg py-2 text-sm font-medium transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ backgroundColor: 'var(--ch8r-accent)', color: 'var(--ch8r-accent-fg)' }}
        >
          {loading ? 'Sending…' : 'Send Message'}
        </button>
      </form>
    </div>
  );
}
