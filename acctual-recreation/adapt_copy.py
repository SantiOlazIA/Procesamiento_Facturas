import os

html_path = r"c:\Users\Tuchi\MiEstudioIA\acctual-recreation\index.html"

with open(html_path, "r", encoding="utf-8") as f:
    text = f.read()

replacements = [
    (
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" class="text-white">\n            <path d="M12 2L2 22H6.5L12 11L17.5 22H22L12 2Z" fill="currentColor" />\n          </svg>',
        '<i data-lucide="cpu" class="w-4 h-4 text-white"></i>'
    ),
    (
        'Acctual\n      </div>',
        'Estudio IA\n      </div>'
    ),
    (
        '<a href="#" class="hover:text-black transition">Teams</a>\n        <a href="#" class="hover:text-black transition">About</a>\n        <a href="#" class="hover:text-black transition">Blog</a>\n        <a href="#" class="hover:text-black transition">Guides</a>',
        '<a href="#workflows" class="hover:text-black transition">Workflows</a>\n        <a href="#services" class="hover:text-black transition">Services</a>\n        <a href="#pricing" class="hover:text-black transition">Pricing</a>'
    ),
    (
        '<div class="flex items-center gap-6 text-[15px] font-semibold">\n        <a href="#" class="hidden md:block hover:text-custom-gray transition">Log in</a>\n        <a href="#" class="bg-black text-white px-8 py-3.5 rounded-full hover:bg-gray-800 transition shadow-lg hover:shadow-xl hover:-translate-y-0.5 transform duration-200">Sign up for\n          free</a>\n      </div>',
        '<div class="flex items-center gap-6 text-[15px] font-semibold">\n        <a href="mailto:contact@estudioia.com" class="bg-black text-white px-8 py-3.5 rounded-full hover:bg-gray-800 transition shadow-lg hover:shadow-xl hover:-translate-y-0.5 transform duration-200">Hire Us</a>\n      </div>'
    ),
    (
        '"Wait that was the easiest invoice I\'ve ever paid lol"',
        '"Parsed 20k rows and audited code in 1.4s! ⚡"'
    ),
    (
        'Simone Penzl',
        'Happy Client'
    ),
    (
        '<img src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=60&h=60"\n          alt="Avatar" class="w-8 h-8 rounded-full object-cover shadow-sm">',
        '<div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center shadow-sm"><i data-lucide="zap" class="w-4 h-4 text-green-600"></i></div>'
    ),
    (
        'Get paid <br class="hidden md:block" /> same day',
        'Automate your <br class="hidden md:block" /> business today'
    ),
    (
        'By sending customers the most flexible invoice on the planet.',
        'Transform manual tasks into seamless automated workflows, from data parsing to complex code auditing.'
    ),
    (
        '<button\n        class="bg-[#0f0f0f] text-white px-12 py-5 rounded-full text-xl font-bold hover:scale-[1.02] hover:bg-black transition-all duration-300 shadow-[0_20px_40px_rgba(0,0,0,0.15)] mb-32 relative z-20 group">\n        Create invoice in seconds',
        '<a href="#workflows"\n        class="inline-block bg-[#0f0f0f] text-white px-12 py-5 rounded-full text-xl font-bold hover:scale-[1.02] hover:bg-black transition-all duration-300 shadow-[0_20px_40px_rgba(0,0,0,0.15)] mb-32 relative z-20 group">\n        Explore our workflows'
    ),
    (
        '<div class="absolute inset-0 rounded-full bg-white opacity-0 group-hover:opacity-10 transition-opacity"></div>\n      </button>',
        '<div class="absolute inset-0 rounded-full bg-white opacity-0 group-hover:opacity-10 transition-opacity"></div>\n      </a>'
    ),
    (
        'Used by 5,000+ businesses globally',
        'Trusted by forward-thinking teams'
    ),
    (
        '<div class="relative w-full max-w-5xl mx-auto h-[600px] mt-10 z-10 flex justify-center">',
        '<div id="workflows" class="relative w-full max-w-5xl mx-auto h-[600px] mt-10 z-10 flex justify-center scroll-mt-32">'
    ),
    (
        'M</div>\n            <div>\n              <h3 class="font-extrabold text-xl text-black">Marble Studio</h3>\n              <p class="text-gray-400 text-[13px] font-medium flex items-center gap-1"><i data-lucide="map-pin"',
        'DP</div>\n            <div>\n              <h3 class="font-extrabold text-xl text-black">Compras LN Pipeline</h3>\n              <p class="text-gray-400 text-[13px] font-medium flex items-center gap-1"><i data-lucide="file-spreadsheet"'
    ),
    (
        'Libertador Avenue 101, AR',
        'Excel Data Transformation'
    ),
    ('Amount due', 'Rows Processed'),
    ('4,500.00 USDC', '45,200'),
    ('Due date', 'Time Saved'),
    ('Oct 24, 2023', '12h/week'),
    ('Client Pays', 'Input Data'),
    ('<i data-lucide="dollar-sign" class="w-3.5 h-3.5"></i></div> USDC', '<i data-lucide="file" class="w-3.5 h-3.5"></i></div> Excel'),
    ('You Receive', 'Output Data'),
    ('₮</div> USDT', '<i data-lucide="check" class="w-3.5 h-3.5 text-white"></i></div> Ledger'),
    (
        'C</div>\n            <div>\n              <h3 class="font-extrabold text-xl text-black">Charm AI</h3>\n              <p class="text-gray-400 text-[13px] font-medium flex items-center gap-1"><i data-lucide="map-pin"',
        'CA</div>\n            <div>\n              <h3 class="font-extrabold text-xl text-black">Hybrid Code Auditor</h3>\n              <p class="text-gray-400 text-[13px] font-medium flex items-center gap-1"><i data-lucide="code"'
    ),
    ('Bengaluru, IN', 'Python & Architecture'),
    ('NVM, Paid!', 'Zero Bugs Found!'),
    ('Paid\n            </div>', 'PASS\n            </div>'),
    ('Invoice #', 'Target File'),
    ('INV-0042', 'core_logic.py'),
    ('Total', 'Issues Found'),
    ('$8,200.00', '0'),
    ('Received', 'Architecture'),
    ('Just now', 'Compliant'),
    (
        '<!-- Map Section (New) -->\n  <section class="w-full bg-[#f9fafb] py-40 relative flex flex-col items-center">',
        '<!-- Map Section (New) -->\n  <section id="services" class="w-full bg-[#f9fafb] py-40 relative flex flex-col items-center">'
    ),
    ('Euros, dollars, yens... <br />', 'Data pipelines, code audits, UI... <br />'),
    ('we do it all, and fast.', 'we build it all, and fast.'),
    ('Prashant <span class="text-gray-400 font-medium">sent an invoice...</span>', 'FCI Pipeline <span class="text-gray-400 font-medium">processed 50 LEDGERs</span>'),
    ('San Francisco, USA', 'PDF Data Extraction'),
    ('Basil <span class="text-gray-400 font-medium">received payment!</span>', 'Website Replication <span class="text-gray-400 font-medium">deployed to production</span>'),
    ('Mumbai, IND', 'Pixel-perfect UI'),
    (
        '<!-- Pricing Section -->\n  <section class="w-full bg-white py-40 flex flex-col items-center">',
        '<!-- Pricing Section -->\n  <section id="pricing" class="w-full bg-white py-40 flex flex-col items-center">'
    ),
    ('With simple pricing', 'Simple, transparent pricing'),
    ('Invoicing', 'Unlimited Automation'),
    ('>1%<', '>$2,500<'),
    ('/ per payment', '/ per month'),
    ('Or <strong class="text-black">0%</strong> when paid with the same method.', 'Pause or cancel anytime. <strong class="text-black">No long-term contracts.</strong>'),
    ('Local bank transfers', 'Custom data pipelines (Excel/PDF)'),
    ('Global cards & ACH', 'Automated hybrid code auditing'),
    ('Crypto rails (USDC/USDT)', 'Pixel-perfect UI replication'),
    ('Automated accounting', 'Dedicated priority support'),
    ('Get started', 'Hire Us'),
    ('Focus on your product, not payments 🚀', 'Focus on your product, not manual work 🚀'),
    ('Dear business owner,', 'Dear founder,'),
    (
        "We built Acctual because we were tired of losing 3-5% on international payments and waiting days for money to arrive. We've talked to hundreds of founders, freelancers, and agencies who feel the exact same pain. It shouldn't be this hard to get paid for your hard work.",
        "We built Estudio IA because we were tired of manually processing spreadsheets, writing boilerplate UI, and missing subtle bugs in code reviews. It shouldn't be this hard to scale your operations and ensure flawless data integrity."
    ),
    (
        "That's why we're combining traditional banking rails with global crypto infrastructure to make cross-border B2B payments instant and nearly free.",
        "That's why we're combining intelligent AI agents, custom scripts, and modern web frameworks to give you your time back and completely eliminate human error."
    ),
    ('Atikh Rana', 'Tuchi'),
    ('CEO & Co-founder', 'Lead Automation Engineer')
]

for old, new in replacements:
    if old in text:
        text = text.replace(old, new)
        print(f"Replaced: {old[:30]}...")
    else:
        print(f"NOT FOUND: {old[:30]}...")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Done updating copy.")
