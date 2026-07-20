export interface SampleTicket {
  id: string;
  label: string;
  category: string;
  ticket: string;
}

export const SAMPLE_TICKETS: SampleTicket[] = [
  {
    id: 'billing',
    label: 'Billing Issue',
    category: 'Billing',
    ticket: `Subject: Duplicate charge on my account

Hi, I'm Sarah Mitchell (sarah.mitchell@example.com, account AC-78234).
I was charged $49.99 twice for my monthly subscription on June 15th.
I have been a loyal customer for over two years and this is the first
time I've encountered a billing error. The duplicate charge appears
on my credit card ending in 4401. I would like the erroneous charge
reversed immediately and confirmation sent to my email on file.
Please escalate if necessary. Thank you.`,
  },
  {
    id: 'shipping',
    label: 'Shipping Delay',
    category: 'Shipping',
    ticket: `Subject: Order #ORD-55231 still not delivered

Hello, I'm James Kowalski (james.k@example.com). I placed an order
for a wireless keyboard (model KB-9000) on May 28th with express
shipping. The estimated delivery was May 31st, but it is now June 4th
and tracking still shows "In Transit" with no updates since May 30th.
The order total was $89.97 including shipping. I need this urgently
as my current keyboard is broken. Please investigate and provide an
ETA or issue a replacement with overnight shipping.`,
  },
  {
    id: 'technical',
    label: 'Technical Issue',
    category: 'Technical Issue',
    ticket: `Subject: App crashes on login — urgent

Hi support, I'm Aisha Patel (aisha.p@example.com, acct AC-90123).
Since updating to v3.2.1 on iOS, the app crashes immediately after
I enter my credentials and tap "Sign In". I have tried reinstalling,
restarting my phone (iPhone 14 Pro, iOS 17.5), and clearing cache.
Nothing works. I have an important client meeting at 3pm where I need
to access my dashboard. Please prioritize. Error log attached below.
Crash report ID: CRASH-7712.`,
  },
  {
    id: 'refund',
    label: 'Refund Request',
    category: 'Refund',
    ticket: `Subject: Requesting full refund — service not as advertised

Hi, I'm Carlos Mendez (carlos.mendez@example.com). I purchased the
Enterprise plan ($299/mo) on May 1st under order ORD-44109. The
product was marketed as having real-time collaboration, but my team
consistently experiences 30+ second sync delays. I contacted support
twice (tickets #TKT-4401 and #TKT-4412) with no resolution. I am
requesting a full refund for the month of May ($299). I have already
migrated to a competitor. Please process within 5 business days.`,
  },
  {
    id: 'account',
    label: 'Account Problem',
    category: 'Account Problem',
    ticket: `Subject: Cannot access account — 2FA loop

Hello, I'm David Kim (david.kim@example.com, account AC-66184).
I recently got a new phone and transferred my 2FA authenticator,
but now when I log in, it keeps asking me to "register a new device"
even though I already did. I'm stuck in a loop. I have tried:
1) Clearing browser cache — no change
2) Using incognito mode — same issue
3) Different browser (Chrome, Safari, Firefox) — all same
I need access to my workspace immediately for a deadline.
Please disable 2FA temporarily or provide a backup code.`,
  },
];

export const SAMPLE_TICKET = SAMPLE_TICKETS[0].ticket;
