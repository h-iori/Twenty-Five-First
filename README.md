# Twenty-Five First (TFF) | Enterprise Grade Full Stack E-Commerce Platform

[![Django](https://img.shields.io/badge/Django-5.2-092e20?logo=django)](https://www.djangoproject.com/)
[![Celery](https://img.shields.io/badge/Celery-5.5-37814a?logo=celery)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-6.4-dc382d?logo=redis)](https://redis.io/)
[![Meilisearch](https://img.shields.io/badge/Meilisearch-0.40-ff5c5c?logo=meilisearch)](https://www.meilisearch.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-336791?logo=postgresql)](https://www.postgresql.org/)
[![Custom Admin](https://img.shields.io/badge/Custom%20Admin-Full%20Featured-6a1b9a?logo=react)](https://example.com)
[![Security](https://img.shields.io/badge/2FA%20+%20Rate%20Limit-Enterprise%20Grade-00bfa5)](https://example.com)
[![Stars](https://img.shields.io/github/stars/h-iori/twentyfivefirst.svg?style=social)](https://github.com/h-iori/Twenty-Five-First)

**Twenty-Five First** is a proprietary, high-performance enterprise e-commerce platform built exclusively for a live, running business. This is a private freelance project developed from the ground up using modern Django architecture. The complete source code is not publicly available and will remain closed-source due to security, intellectual property, and client confidentiality reasons. The product should not be used by anyone; it is my own property. I provide this kind of project services for clients.

Only selected architectural highlights, custom admin capabilities, and technical design decisions are showcased in this README for portfolio and demonstration purposes. This project is/Will be deployed and actively serving real customers.

**Live URL**: https://twentyfivefirst.com

**Alternate URL**: http://13.232.137.94

---

## 🌟 Why Twenty-Five First Stands Alone

In a sea of cookie-cutter SaaS solutions, Twenty-Five First emerges as the crown jewel for discerning founders and engineering leaders who refuse to compromise:

- **Extreme Scalability by Design**: Distributed task queues, multi-layer Redis caching, and PostgreSQL GIN indexing ensure millions of concurrent users feel like a breeze.
- **Strong Search-Engine (Meilisearch)**: Uses the full power of industru grade search engine Meilisearch for instant product search.
- **Operational Intelligence at Scale**: Real-time sidebar alerts for pending orders, low-stock variants, expiring coupons, open tickets, and bulk queries—your team never misses a beat.
- **Conversion Mastery**: Abandoned-cart recovery, personalized review prompts on delivery, dynamic pricing with tax calculation (5%/18%), and guest-checkout unification.
- **Security Without Sacrifices**: Full 2FA (email OTP), per-IP/email rate limiting with 1-hour blocks, concurrency tokens, soft-delete audit trails, and atomic transaction wrappers.
- **Developer Velocity**: Service-utility pattern, exhaustive prefetching, cached dashboard stats, modular signals, and comprehensive bulk actions reduce maintenance to near-zero.
- **Regulatory Excellence**: GST-compliant invoices with CGST/SGST/IGST splitting, HSN codes, financial-year sequencing, and Maharashtra supplier defaults.
- **SEO Supremacy**: Auto-generated enterprise schema (Product, AggregateOffer, MerchantReturnPolicy, BreadcrumbList), color-specific slugs, dynamic sitemaps, and robots.txt control.
- **Custom Admin Supremacy**: A bespoke, high-performance admin panel (not Django admin) featuring AJAX modals, advanced filtering, usage history pagination, PDF preview, CSV streaming exports, and recycle-bin restoration.

Twenty-Five First is engineered for brands that demand both beauty and unbreakable performance—turning technical excellence into measurable revenue.

---

## 📸 Visual Showcase

![Project Banner](https://via.placeholder.com/1200x400?text=Twenty-Five+First+-+Where+Code+Meets+Commerce)

### Customer-Facing Elegance
| Home Page | Product Details Page | Checkout Page |
| :---: | :---: | :---: |
| ![Home](https://via.placeholder.com/400x250?text=Hero+Home+Page) | ![Product Details](https://via.placeholder.com/400x250?text=Product+Detail+View) | ![Checkout](https://via.placeholder.com/400x250?text=Full+Checkout+Process) |

### Command Center: Custom Admin Mastery
| Admin Dashboard | Order Details | Download Invoice PDF |
| :---: | :---: | :---: |
| ![Dashboard](https://via.placeholder.com/400x250?text=Admin+Dashboard+View) | ![Order Details](https://via.placeholder.com/400x250?text=Order+Details+Modal) | ![PDF Download](https://via.placeholder.com/400x250?text=Admin+Invoice+PDF) |

| Recycle Bin | Real-Time Sidebar Notifications |
| :---: | :---: |
| ![Recycle Bin](https://via.placeholder.com/400x250?text=Admin+Recycle+Bin) | ![Notifications](https://via.placeholder.com/400x250?text=Admin+Sidebar+Notifications) |

These are not mockups—they are windows into a living, breathing enterprise system.

---

## 🏰 The Custom Admin Command Center: A Masterpiece of Control

Replacing the default Django admin entirely, TFF’s bespoke admin panel is a high-velocity operations cockpit built for real-world scale:

- Secure 2FA with email OTP + Redis concurrency tokens + per-IP/email rate limiting
- Live sidebar with 10 real-time indicators (pending orders, returns, cancels, low-stock <10, new reviews <24h, expiring coupons <3 days, today’s customers/guests, open tickets, pending bulk queries).
- Order Command Hub: Advanced filtering (status, payment, verification, coupon, user-type, amount range, date range), sortable columns, AJAX detail modals showing items with primary images, shipping/payment breakdowns, status/payment/verification triple-update, bulk status/delete.
- Review & Feedback Control: Rating/product/user/date filters, bulk delete, inline editing modal.
- Coupon Intelligence Suite: Full CRUD, usage-history pagination with user/order links, validity filters, bulk activate/deactivate/delete, proportional discount validation.
- Support & Bulk Query: Status/date filters, bulk status updates, detailed modals.
- Guest & Customer Mastery: Separate guest/customer panels with address CRUD, ban/unban, order/review/wishlist/history counts, bulk ban/delete.
- Cancellation & Return Arbitration: Approve/reject with admin notes, automatic order status sync (CANCELLED/RETURNED), image attachments, bulk actions.
- Invoice & Financial Command: GST-compliant listing with FY/state/amount filters, AJAX HTML preview, one-click WeasyPrint PDF download, streaming CSV export (GST-ready format with taxable value, tax rates, place-of-supply).
- Product & Inventory Forge: Variant/color/media management, live stock adjustment by SKU, attribute CRUD (ShirtType/Material/Pattern/Color with hex), bulk status toggle, soft-delete recycle bin.
- Recycle Bin Recovery: Soft-deleted Orders/Invoices/Reviews/Coupons/Customers/Guests/Tickets/Bulk-Requests with single/bulk restore/permanent hard-delete and field-level detail view.

Every interaction is cached where possible, prefetched aggressively, and protected by `@secure_admin_required` and `@csrf_protect`. This is not an admin—it is a mission control center.

---

## ✨ Core Capabilities

- Real-time cart abandonment recovery (Celery Beat every 30 min)
- Guest + authenticated cart merging with Redis snapshots
- Dynamic tax calculation (5% under ₹2500, 18% above) + HSN 6205
- Enterprise SEO: color-specific slugs, JSON-LD Product/AggregateOffer/MerchantReturnPolicy
- Soft-delete everywhere with audit timestamps and cascade restore
- Signal-driven automation (SEO regeneration, invoice creation on SHIPPED, welcome emails, status updates)
- WeasyPrint GST invoices with supplier defaults (Maharashtra GSTIN)
- Streaming CSV export for compliance

---

## ⚙️ Technology Symphony

- Backend: Django 5.2 (Service-Utility Pattern)
- Orchestration: Celery 5.5 + Redis 6.4 (dedicated emails queue)
- Database: PostgreSQL 18 (GIN indexes, select_related/prefetch_related)
- Search: Meilisearch 0.40 (real-time indexing via signals)
- Caching: Redis (API, sessions, carts)
- Payments: Razorpay (atomic creation + HMAC webhook verification)
- Logistics: Shiprocket (real-time estimates, pickup scheduling)
- PDF: WeasyPrint (GST-compliant, dynamic styling)
- Admin: 100% Custom (AJAX-heavy, no Django admin dependency)

---

## 🏗️ Architectural Brilliance

- **Service-Utility Pattern**: All business logic lives in dedicated services—views remain thin and testable.
- **Signal Ecosystem**: Post-save/post-delete signals automatically regenerate SEO, update parent stock, invalidate invoice caches, send transactional emails asynchronously.
- **Distributed Locks**: Redis `redis_lock` prevents race conditions in stock deduction and cart merging.
- **Multi-Layer Caching**: MD5-hashed query caching, Redis sessions/carts, per-model cache invalidation.
- **Soft-Delete Foundation**: Every critical model inherits `SoftDeleteModel` with queryset manager separation and cascade restore.
- **Admin Security Layer**: 2FA OTP (cached + idempotency), concurrency tokens, per-action rate limiting, failed-attempt blocking.

---

## 🔒 Security & Compliance Fortress

- 2FA + OTP rate limiting (separate login/OTP buckets)
- IP/email-based temporary blocks (1 hour)
- Concurrency token per admin session (Redis)
- HMAC-SHA256 webhook verification (Razorpay)
- All critical paths wrapped in `transaction.atomic()`
- Soft-delete audit trail + recycle bin for forensic recovery
- GST-compliant invoicing with correct CGST/SGST/IGST splitting

---

## 🚀 Performance & Scalability Engine

- Horizontal worker scaling (multiple Celery nodes)
- Redis connection pooling (max_connections=1000)
- Query optimization (select_related, prefetch_related, annotate aggregates)
- API response caching with versioned keys
- Gunicorn + Nginx ready for production
- Prepared for CDN (static/media) and database read replicas

---

## 🔍 SEO & Discoverability Mastery

- Color-variant-specific slugs and meta
- Auto-generated JSON-LD (Product, AggregateOffer, MerchantReturnPolicy, ShippingDetails, BreadcrumbList)
- Optimized ProductSitemap (daily, priority 1.0) and StaticViewSitemap (high-value pages only)
- Dynamic robots.txt
- SearchVectorField fallback + Meilisearch primary

---

## 🛤️ Future Roadmap

- AI-powered product recommendations & dynamic pricing
- Multi-vendor marketplace support
- Internationalization & multi-currency
- Mobile companion app

---

## 💼 Freelance Services Offered

I specialize in delivering production-grade, secure, and scalable Django e-commerce solutions for live businesses, including:

- Custom high-performance admin panels (no default Django admin)
- Razorpay + Shiprocket + Meilisearch + GST invoice integrations
- Advanced automation, soft-delete systems, and real-time search
- Secure authentication, rate limiting, and concurrency control
- Full-stack enterprise architecture with emphasis on maintainability and speed

Available for freelance projects. Contact for custom development inquiries.

---

## 📄 Legal Notice

© 2026 Harsh Upadhyay. All Rights Reserved.  
This software, its source code, architecture, design, and documentation are the exclusive intellectual property of the developer and the commissioning client. Any unauthorized use, copying, distribution, or reverse-engineering is strictly prohibited and will be pursued legally.

Full codebase is private and hidden for security and confidentiality reasons. This README serves solely as a professional portfolio showcase of capabilities and architectural decisions.

---

**Developed with ❤️ and relentless ambition by Harsh Upadhyay**  
*Showcasing enterprise Django architecture, custom admin mastery, distributed systems design, and a passion for turning technical excellence into unstoppable business growth.*
