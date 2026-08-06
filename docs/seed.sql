--
-- PostgreSQL database dump
--

-- Dumped from database version 14.10 (Homebrew)
-- Dumped by pg_dump version 14.10 (Homebrew)

-- Started on 2026-08-06 23:35:53 JST

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 3643 (class 0 OID 24892)
-- Dependencies: 214
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.categories VALUES (1, 'livestyle', '2026-08-01 20:07:44.282369+07');
INSERT INTO public.categories VALUES (2, 'gaming', '2026-08-01 20:07:44.282369+07');
INSERT INTO public.categories VALUES (3, 'apple', '2026-08-01 20:07:44.282369+07');
INSERT INTO public.categories VALUES (4, 'komputer', '2026-08-01 20:07:44.282369+07');


--
-- TOC entry 3641 (class 0 OID 24882)
-- Dependencies: 212
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.products VALUES (1, 'laptop asus', 50, 'asus', '2026-08-01 20:07:33.833666+07', 'laptop dengan batre cepat rusak', 0.00);
INSERT INTO public.products VALUES (2, 'laptop lenovo', 150, 'lenovo', '2026-08-01 20:07:33.833666+07', 'terkenal dengan laptop gaming murahnya', 0.00);
INSERT INTO public.products VALUES (3, 'laptop surface', 30, 'microsoft', '2026-08-01 20:07:33.833666+07', 'laptop dari sang pembuat os dengan harga lebih mahal dari yang lain', 0.00);
INSERT INTO public.products VALUES (4, 'laptop macbook', 50, 'apple', '2026-08-01 20:07:33.833666+07', 'laptop dengan prioritas keamanan yang tinggi', 0.00);


--
-- TOC entry 3644 (class 0 OID 24902)
-- Dependencies: 215
-- Data for Name: category_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.category_items VALUES (1, 1, '2026-08-01 20:07:53.554752+07');
INSERT INTO public.category_items VALUES (2, 2, '2026-08-01 20:07:53.554752+07');
INSERT INTO public.category_items VALUES (3, 4, '2026-08-01 20:07:53.554752+07');
INSERT INTO public.category_items VALUES (4, 4, '2026-08-01 20:07:53.554752+07');


--
-- TOC entry 3639 (class 0 OID 24870)
-- Dependencies: 210
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.users VALUES (1, 'budi@gmail.com', 27, false, 'password', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', '2026-08-01 20:11:02.118738+07');
INSERT INTO public.users VALUES (2, 'arini@gmail.com', 27, false, 'password', '4813494d137e1631bba301d5acab6e7bb7aa74ce1185d456565ef51d737677b2', '2026-08-01 20:11:02.118738+07');
INSERT INTO public.users VALUES (3, 'husni@gmail.com', 27, false, 'password', 'e10adc3949ba59abbe56e057f20f883e28b4b4dbd33b58c4886d22698e7341ea', '2026-08-01 20:11:02.118738+07');


--
-- TOC entry 3646 (class 0 OID 24919)
-- Dependencies: 217
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.orders VALUES (1, 1, 'inv-4229435', 'pending', '2026-08-01 20:11:13.611652+07', 1);
INSERT INTO public.orders VALUES (2, 2, 'inv-3245435', 'pending', '2026-08-01 20:11:13.611652+07', 1);
INSERT INTO public.orders VALUES (3, 3, 'inv-4374343', 'pending', '2026-08-01 20:11:13.611652+07', 1);
INSERT INTO public.orders VALUES (4, 2, 'inv-2938673', 'pending', '2026-08-01 20:11:13.611652+07', 1);


--
-- TOC entry 3648 (class 0 OID 24936)
-- Dependencies: 219
-- Data for Name: order_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.order_items VALUES (1, 1, 4, 35, '2026-08-01 20:11:30.898556+07');
INSERT INTO public.order_items VALUES (2, 2, 2, 28, '2026-08-01 20:11:30.898556+07');
INSERT INTO public.order_items VALUES (3, 3, 2, 100, '2026-08-01 20:11:30.898556+07');
INSERT INTO public.order_items VALUES (4, 1, 3, 1, '2026-08-01 20:11:30.898556+07');


--
-- TOC entry 3654 (class 0 OID 0)
-- Dependencies: 213
-- Name: categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.categories_id_seq', 4, true);


--
-- TOC entry 3655 (class 0 OID 0)
-- Dependencies: 218
-- Name: order_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.order_items_id_seq', 4, true);


--
-- TOC entry 3656 (class 0 OID 0)
-- Dependencies: 216
-- Name: orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.orders_id_seq', 4, true);


--
-- TOC entry 3657 (class 0 OID 0)
-- Dependencies: 211
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.products_id_seq', 4, true);


--
-- TOC entry 3658 (class 0 OID 0)
-- Dependencies: 209
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 3, true);


-- Completed on 2026-08-06 23:35:53 JST

--
-- PostgreSQL database dump complete
--

