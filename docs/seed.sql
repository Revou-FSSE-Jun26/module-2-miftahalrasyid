--
-- PostgreSQL database dump
--

-- Dumped from database version 14.10 (Homebrew)
-- Dumped by pg_dump version 14.10 (Homebrew)

-- Started on 2026-08-18 17:02:34 JST

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
-- TOC entry 3664 (class 0 OID 25384)
-- Dependencies: 219
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.alembic_version VALUES ('9a575b777f47');


--
-- TOC entry 3659 (class 0 OID 24892)
-- Dependencies: 214
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.categories VALUES (1, 'livestyle', '2026-08-01 20:07:44.282369+07');
INSERT INTO public.categories VALUES (2, 'gaming', '2026-08-01 20:07:44.282369+07');
INSERT INTO public.categories VALUES (3, 'apple', '2026-08-01 20:07:44.282369+07');
INSERT INTO public.categories VALUES (4, 'komputer', '2026-08-01 20:07:44.282369+07');


--
-- TOC entry 3655 (class 0 OID 24870)
-- Dependencies: 210
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.users VALUES (4, 'angel@gmail.com', 21, false, 'PASSWORD_HASH', '6514970c5ed4c2eb312bc1bb799477cbb8c616c8a798a1a28b175680f738a299', '2026-08-11 23:51:06.434151+07', 'angel', '{BUYER}', '2026-08-15 17:13:06.407376+07');
INSERT INTO public.users VALUES (1, 'budi@gmail.com', 27, false, 'PASSWORD_HASH', '2159cea8efdb8491058156ee571bcc0ce09c896dc591e4a7f840d59c95be771e', '2026-08-01 20:11:02.118738+07', 'budi', '{BUYER}', NULL);
INSERT INTO public.users VALUES (3, 'husni@gmail.com', 27, false, 'PASSWORD_HASH', 'e10adc3949ba59abbe56e057f20f883e28b4b4dbd33b58c4886d22698e7341ea', '2026-08-01 20:11:02.118738+07', 'husni', '{BUYER}', NULL);
INSERT INTO public.users VALUES (2, 'arini@gmail.com', 27, false, 'PASSWORD_HASH', '4813494d137e1631bba301d5acab6e7bb7aa74ce1185d456565ef51d737677b2', '2026-08-01 20:11:02.118738+07', 'arini', '{BUYER,SELLER}', NULL);
INSERT INTO public.users VALUES (5, 'justin@gmail.com', 28, false, 'PASSWORD_HASH', 'a3f0956da3cfb843d8e7ee5d867bf0d4bbdd6955587d235678ab68e13ce67846', '2026-08-11 23:53:06.93869+07', 'justin', '{BUYER}', NULL);
INSERT INTO public.users VALUES (10, 'mike@gmail.com', 18, false, 'PASSWORD_HASH', '1fb0ab1378099448c8800dd96f25409ec10e9ea802c0bcadbf8d322b3e9f94ec', '2026-08-12 01:02:44.353652+07', 'mike', '{BUYER}', NULL);
INSERT INTO public.users VALUES (12, 'adriana@gmail.com', 35, false, 'PASSWORD_HASH', 'f96354dd9b0cb206ba156f52be94e4cdfebad293e834fd8276643942d9e6b83f', '2026-08-12 16:33:27.012421+07', 'adriana', '{BUYER}', NULL);
INSERT INTO public.users VALUES (15, 'budiarie@gmail.com', 70, false, 'PASSWORD_HASH', '375465ccbe9e4c51234b1431066b6c9297a04efe191da70b2b4fabcdacab3245', '2026-08-14 00:21:10.081767+07', 'budiarie', '{BUYER}', NULL);
INSERT INTO public.users VALUES (16, 'rafaelalun@gmail.com', 50, false, 'PASSWORD_HASH', '8470cef960b11e01639514a918479325358725499d546c250152b2fb97307619', '2026-08-14 00:28:02.759062+07', 'rafaelalun', '{BUYER}', NULL);
INSERT INTO public.users VALUES (14, 'funnyclown1112@gmail.com', 35, false, 'PASSWORD_HASH', 'f96354dd9b0cb206ba156f52be94e4cdfebad293e834fd8276643942d9e6b83f', '2026-08-13 14:57:35.817786+07', 'funnyclown1112', '{SUPERADMIN}', '2026-08-15 16:59:42.875204+07');


--
-- TOC entry 3657 (class 0 OID 24882)
-- Dependencies: 212
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.products VALUES (1, 'laptop asus', 50, 'asus', '2026-08-01 20:07:33.833666+07', 'laptop dengan batre cepat rusak', 0.00, 2);
INSERT INTO public.products VALUES (2, 'laptop lenovo', 150, 'lenovo', '2026-08-01 20:07:33.833666+07', 'terkenal dengan laptop gaming murahnya', 0.00, 2);
INSERT INTO public.products VALUES (3, 'laptop surface', 30, 'microsoft', '2026-08-01 20:07:33.833666+07', 'laptop dari sang pembuat os dengan harga lebih mahal dari yang lain', 0.00, 2);
INSERT INTO public.products VALUES (4, 'laptop macbook', 50, 'apple', '2026-08-01 20:07:33.833666+07', 'laptop dengan prioritas keamanan yang tinggi', 0.00, 2);


--
-- TOC entry 3660 (class 0 OID 24902)
-- Dependencies: 215
-- Data for Name: category_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.category_items VALUES (1, 1, '2026-08-01 20:07:53.554752+07');
INSERT INTO public.category_items VALUES (2, 2, '2026-08-01 20:07:53.554752+07');
INSERT INTO public.category_items VALUES (3, 4, '2026-08-01 20:07:53.554752+07');
INSERT INTO public.category_items VALUES (4, 4, '2026-08-01 20:07:53.554752+07');


--
-- TOC entry 3662 (class 0 OID 24919)
-- Dependencies: 217
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.orders VALUES (1, 1, 'inv-4229435', 'PENDING', '2026-08-01 20:11:13.611652+07', 1.00);
INSERT INTO public.orders VALUES (2, 2, 'inv-3245435', 'PENDING', '2026-08-01 20:11:13.611652+07', 1.00);
INSERT INTO public.orders VALUES (3, 3, 'inv-4374343', 'PENDING', '2026-08-01 20:11:13.611652+07', 1.00);
INSERT INTO public.orders VALUES (4, 2, 'inv-2938673', 'PENDING', '2026-08-01 20:11:13.611652+07', 1.00);


--
-- TOC entry 3663 (class 0 OID 24936)
-- Dependencies: 218
-- Data for Name: order_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.order_items VALUES (1, 4, '2026-08-01 20:11:30.898556+07', 1, 1, 0.00, NULL);
INSERT INTO public.order_items VALUES (2, 2, '2026-08-01 20:11:30.898556+07', 2, 1, 0.00, NULL);
INSERT INTO public.order_items VALUES (3, 2, '2026-08-01 20:11:30.898556+07', 3, 1, 0.00, NULL);
INSERT INTO public.order_items VALUES (1, 3, '2026-08-01 20:11:30.898556+07', 4, 1, 0.00, NULL);


--
-- TOC entry 3671 (class 0 OID 0)
-- Dependencies: 213
-- Name: categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.categories_id_seq', 4, true);


--
-- TOC entry 3672 (class 0 OID 0)
-- Dependencies: 220
-- Name: order_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.order_items_id_seq', 4, true);


--
-- TOC entry 3673 (class 0 OID 0)
-- Dependencies: 216
-- Name: orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.orders_id_seq', 4, true);


--
-- TOC entry 3674 (class 0 OID 0)
-- Dependencies: 211
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.products_id_seq', 4, true);


--
-- TOC entry 3675 (class 0 OID 0)
-- Dependencies: 209
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 31, true);


-- Completed on 2026-08-18 17:02:34 JST

--
-- PostgreSQL database dump complete
--

