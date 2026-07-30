# RevoShop (Backend) — Project Plan

## Overview

RevoShop is an intuitive e-commerce ecosystem that simplifies online transactions for buyers and sellers alike. Our secure database allows customers to track history and plan future purchases, while robust inventory management tools empower sellers to dynamically adjust stock levels to meet customer demand.

## SDLC Plan

| Phase | Who is Responsible | Activity for This Project |
|-------|-------------------|--------------------------|
| Plan | Product Owner | Make a business plan. Create core feature requirements. Decide the software development method (Agile,etc). create development timeline |
| Design | UX/UI Designer / System Architect | Create user interface wireframes and mockups. Design system architecture, database schemas, and data flow diagrams. |
| Develop | Software Engineers / Developers | Write clean, scalable source code. Build the front-end interface and back-end logic. Conduct initial developer code reviews. |
| Test | QA Engineers / Testers | Write and execute test plans. Find, log, and track software bugs. Verify that the software meets original feature requirements. |
| Deploy | DevOps Engineers / Release Manager | Package the code. Set up live server environments. Release the finished software to production so users can access it. |
| Maintain | Support Team / Maintenance Engineers | Monitor system performance. Fix live bugs reported by real users. Release patches, security updates, and small system improvements. |

## Functional Requirements

- Users can register on RevoShop.
- Users receive an email confirmation after registering.
- Users can log in using their registered email and password.
- Users can have buyer and seller features.
- Users can Create, Update, and Delete a `products`
- Users can Create, Update, and Delete a `categories`
- Users can group their `products` into `categories`
- Users can place an order

## Risks & Mitigations

- **Risk 1:** Delivery timeline compression may result in incomplete project deliverables.
**Mitigation:** Implement a phased delivery plan to prioritize core features first, ensuring a viable product is delivered on time even if smaller tasks are delayed.

## Developer Tools

- **Terminal:** used for communicating with the server on the network
- **Git:** project versioning to ensure scalability
- **VS Code:** vast amount of extensions to support clean and scalable coding
- **PostgreSql:** needed for complicated query and acid-compliant development

## Database Design

| Name |  Column  |
|-------|--------------------------|
| `users` | `name`, `email`, `age`,`is_active`, `provider`, `providerKey`, `created_at`|
| `products` | `name`, `quantity`, `brand`, `created_at`, `updated_at` |

- **Tables:** `users`,`categories`,`products`,`orders`,and `order_items` as *junction table*