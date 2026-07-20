export interface ExampleTicket {
  id: string;
  label: string;
  icon: string;
  ticket: string;
}

export const EXAMPLE_TICKETS: ExampleTicket[] = [
  {
    id: 'outage',
    label: 'Internet outage',
    icon: 'wifi',
    ticket: `Subject: Internet completely down for 3 days

Hi, I'm Marcus Chen (marcus.chen@example.com, account AC-55210).
My home internet has been totally down since Tuesday morning. I've rebooted
the router 4 times, checked all cables, and nothing works. I work from home
so this is costing me money every day. I need a technician dispatched ASAP.
Ticket #OUT-9921. Please escalate — this is urgent.`,
  },
  {
    id: 'refund',
    label: 'Refund request',
    icon: 'refund',
    ticket: `Subject: Double charged — need refund ASAP

Hi support team, I'm Jordan Avery (jordan.avery@example.com). I was charged
TWICE for my annual subscription this morning. Order ID ORD-88421, $240 each,
so $480 total taken from my account. I've been a customer for 3 years. I need
the duplicate $240 refunded to the same card immediately, and a small goodwill
credit would be appreciated. Please confirm once processed.`,
  },
  {
    id: 'payment',
    label: 'Payment failed',
    icon: 'card',
    ticket: `Subject: Payment won't go through

Hello, I'm Priya Sharma (priya.sharma@example.com). I'm trying to upgrade to
the Pro plan ($49/mo) but my card keeps getting declined with error code
PAY-DECLINED-402. I've tried two different cards, both valid with sufficient
funds. My account is AC-30455. Can you check if there's a block on my account
or a system issue? I need this resolved today.`,
  },
  {
    id: 'locked',
    label: 'Account locked',
    icon: 'lock',
    ticket: `Subject: Account locked me out

Hi, I'm Devon Park (devon.park@example.com, account AC-77812). I tried logging
in this morning and got "Account temporarily locked for security reasons."
I did not trigger this — no failed login attempts on my end. I have 2FA enabled
via authenticator app. Please unlock my account and tell me what triggered the
lock. I have a demo at 2pm and need access urgently.`,
  },
  {
    id: 'shipping',
    label: 'Shipping delay',
    icon: 'truck',
    ticket: `Subject: Order never arrived — 2 weeks late

Hello, I'm Riley Okonkwo (riley.o@example.com). I placed order ORD-45521 on
March 3rd, standard shipping, supposed to arrive in 5-7 days. It's now March
17th and still nothing. Tracking shows "label created" but no movement since
March 4th. The order contains a $320 monitor I need for work. Either ship a
replacement overnight or refund me. Order total was $387.50.`,
  },
];
