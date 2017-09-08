--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.5
-- Dumped by pg_dump version 9.6.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: network_interfaces; Type: TABLE; Schema: public; Owner: awathen
--

CREATE TABLE network_interfaces (
    hostname character varying(20),
    interface character varying(20),
    ip_address inet,
    protocol_status character varying(5),
    status character varying(5)
);


ALTER TABLE network_interfaces OWNER TO postgresql;

--
-- Data for Name: network_interfaces; Type: TABLE DATA; Schema: public; Owner: awathen
--

COPY network_interfaces (hostname, interface, ip_address, protocol_status, status) FROM stdin;
CSR1000V5	GigabitEthernet2	10.51.60.40	up	up
CSR1000V1	GigabitEthernet2	10.51.60.36	up	up
CSR1000V2	GigabitEthernet2	10.51.60.37	up	up
CSR1000V3	GigabitEthernet2	10.51.60.38	up	up
CSR1000V6	GigabitEthernet2	10.51.60.41	up	up
CSR1000V7	GigabitEthernet2	10.51.60.42	up	up
CSR1000V8	GigabitEthernet2	10.51.60.43	up	up
CSR1000V9	GigabitEthernet2	10.51.60.44	up	up
CSR1000V10	GigabitEthernet2	10.51.60.45	up	up
CSR1000V4	GigabitEthernet2	10.51.60.39	up	up
\.


--
-- PostgreSQL database dump complete
--

