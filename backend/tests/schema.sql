--
-- PostgreSQL database dump
--


-- Dumped from database version 16.13 (Homebrew)
-- Dumped by pg_dump version 16.13 (Homebrew)

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
-- Name: log_order_status_change(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.log_order_status_change() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF OLD.status IS DISTINCT FROM NEW.status THEN
    INSERT INTO order_status_log (order_id, old_status, new_status)
    VALUES (NEW.id, OLD.status, NEW.status);
  END IF;
  RETURN NEW;
END;
$$;


--
-- Name: set_brands_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_brands_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


--
-- Name: set_categories_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_categories_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


--
-- Name: set_customer_addresses_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_customer_addresses_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


--
-- Name: set_customer_tokens_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_customer_tokens_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


--
-- Name: set_model_categories_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_model_categories_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


--
-- Name: set_models_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_models_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


--
-- Name: set_order_items_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_order_items_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


--
-- Name: set_price_overrides_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_price_overrides_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


--
-- Name: set_product_types_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_product_types_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


--
-- Name: set_service_items_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_service_items_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


--
-- Name: set_service_types_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_service_types_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


--
-- Name: set_special_service_records_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_special_service_records_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


--
-- Name: set_special_services_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_special_services_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


--
-- Name: set_staff_tokens_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_staff_tokens_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


--
-- Name: set_staff_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_staff_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


--
-- Name: set_tracking_nodes_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_tracking_nodes_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


--
-- Name: update_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: brands; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.brands (
    id integer NOT NULL,
    product_type_id integer,
    name text NOT NULL,
    country text DEFAULT ''::text,
    website text DEFAULT ''::text,
    notes text DEFAULT ''::text,
    is_active integer DEFAULT 1,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: brands_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.brands_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: brands_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.brands_id_seq OWNED BY public.brands.id;


--
-- Name: categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.categories (
    id integer NOT NULL,
    name text NOT NULL,
    description text,
    sort_order integer DEFAULT 0,
    is_active integer DEFAULT 1,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: categories_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.categories_id_seq OWNED BY public.categories.id;


--
-- Name: customer_addresses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_addresses (
    id integer NOT NULL,
    customer_id integer NOT NULL,
    receiver_name text DEFAULT ''::text,
    receiver_phone text DEFAULT ''::text,
    receiver_address text DEFAULT ''::text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: customer_addresses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.customer_addresses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: customer_addresses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.customer_addresses_id_seq OWNED BY public.customer_addresses.id;


--
-- Name: customer_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_tokens (
    id integer NOT NULL,
    customer_id integer NOT NULL,
    token text NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: customer_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.customer_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: customer_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.customer_tokens_id_seq OWNED BY public.customer_tokens.id;


--
-- Name: customers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customers (
    id integer NOT NULL,
    openid text,
    nickname text DEFAULT ''::text,
    avatar_url text DEFAULT ''::text,
    phone text DEFAULT ''::text,
    name text DEFAULT ''::text,
    address text DEFAULT ''::text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    is_dealer integer DEFAULT 0,
    discount_rate real DEFAULT 100
);


--
-- Name: COLUMN customers.is_dealer; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.customers.is_dealer IS '是否经销商 0=否 1=是';


--
-- Name: COLUMN customers.discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.customers.discount_rate IS '折扣比例，如85表示85折';


--
-- Name: customers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.customers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: customers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.customers_id_seq OWNED BY public.customers.id;


--
-- Name: equipment_inspection_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.equipment_inspection_data (
    id integer NOT NULL,
    order_item_id integer NOT NULL,
    order_id integer NOT NULL,
    first_stage_count integer DEFAULT 1,
    first_stage_serials text[],
    first_stage_pre_pressure text[],
    first_stage_post_pressure text[],
    second_stage_count integer DEFAULT 1,
    second_stage_serials text[],
    second_stage_pre_resistance text[],
    second_stage_post_resistance text[],
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    staff_id integer,
    staff_name text
);


--
-- Name: equipment_inspection_data_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.equipment_inspection_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: equipment_inspection_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.equipment_inspection_data_id_seq OWNED BY public.equipment_inspection_data.id;


--
-- Name: maintenance_reminders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.maintenance_reminders (
    id integer NOT NULL,
    order_id integer,
    customer_id integer,
    equipment_summary text DEFAULT ''::text NOT NULL,
    last_service_date timestamp with time zone,
    next_service_date timestamp with time zone NOT NULL,
    reminder_sent boolean DEFAULT false,
    reminder_sent_at timestamp with time zone,
    notify_count integer DEFAULT 0,
    status character varying(20) DEFAULT 'pending'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT maintenance_reminders_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'sent'::character varying, 'dismissed'::character varying, 'overdue'::character varying])::text[])))
);


--
-- Name: maintenance_reminders_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.maintenance_reminders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: maintenance_reminders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.maintenance_reminders_id_seq OWNED BY public.maintenance_reminders.id;


--
-- Name: model_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.model_categories (
    id integer NOT NULL,
    model_id integer NOT NULL,
    category_id integer NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: model_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.model_categories_id_seq OWNED BY public.model_categories.id;


--
-- Name: models; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.models (
    id integer NOT NULL,
    brand_id integer,
    name text NOT NULL,
    is_active integer DEFAULT 1,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    category text,
    serial_no text DEFAULT ''::text,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: models_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.models_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: models_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.models_id_seq OWNED BY public.models.id;


--
-- Name: order_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_items (
    id integer NOT NULL,
    order_id integer,
    product_type_id integer,
    brand_id integer,
    model_id integer,
    quantity integer DEFAULT 1,
    service_type_id integer,
    item_price real DEFAULT 0,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    category text DEFAULT ''::text,
    customer_note text DEFAULT ''::text NOT NULL,
    brand_name_text text DEFAULT ''::text,
    model_name_text text DEFAULT ''::text,
    service_name_text text DEFAULT ''::text,
    discount_rate real DEFAULT 100,
    final_price real DEFAULT 0,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: COLUMN order_items.discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.order_items.discount_rate IS '该明细应用的折扣比例';


--
-- Name: COLUMN order_items.final_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.order_items.final_price IS '折扣后的实际单价';


--
-- Name: order_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.order_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: order_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.order_items_id_seq OWNED BY public.order_items.id;


--
-- Name: order_status_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_status_log (
    id integer NOT NULL,
    order_id integer NOT NULL,
    old_status character varying(50),
    new_status character varying(50) NOT NULL,
    changed_by integer,
    changed_at timestamp with time zone DEFAULT now() NOT NULL,
    note text
);


--
-- Name: order_status_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.order_status_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: order_status_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.order_status_log_id_seq OWNED BY public.order_status_log.id;


--
-- Name: orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.orders (
    id integer NOT NULL,
    order_no text NOT NULL,
    customer_id integer,
    receiver_name text DEFAULT ''::text,
    receiver_phone text DEFAULT ''::text,
    receiver_address text DEFAULT ''::text,
    total_amount real DEFAULT 0,
    freight_amount real DEFAULT 0,
    status text DEFAULT 'pending'::text,
    payment_status text DEFAULT 'unpaid'::text,
    payment_time timestamp without time zone,
    express_company text DEFAULT ''::text,
    express_no text DEFAULT ''::text,
    express_paid_by_customer integer DEFAULT 1,
    return_express_company text DEFAULT ''::text,
    return_express_no text DEFAULT ''::text,
    return_express_paid_by_customer integer DEFAULT 0,
    customer_remark text DEFAULT ''::text,
    staff_remark text DEFAULT ''::text,
    source text DEFAULT 'wechat'::text,
    pdf_path text DEFAULT ''::text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone,
    delivery_type text DEFAULT 'store'::text,
    store_checkin_at timestamp without time zone,
    archived integer DEFAULT 0,
    is_simulation integer DEFAULT 0,
    pdf_available_until text,
    assigned_staff_id integer,
    urgent_service integer DEFAULT 0,
    urgent_fee real DEFAULT 0,
    CONSTRAINT chk_orders_payment_status CHECK ((payment_status = ANY (ARRAY['unpaid'::text, 'paid'::text, 'refunded'::text]))),
    CONSTRAINT chk_orders_status CHECK ((status = ANY (ARRAY['pending'::text, 'confirmed'::text, 'received'::text, 'inspecting'::text, 'repairing'::text, 'qc'::text, 'ready'::text, 'shipped'::text, 'completed'::text, 'deleted'::text, 'cancelled'::text, 'rejected'::text])))
);


--
-- Name: COLUMN orders.urgent_service; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.orders.urgent_service IS '是否加急服务 0=否 1=是';


--
-- Name: COLUMN orders.urgent_fee; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.orders.urgent_fee IS '加急费用金额';


--
-- Name: orders_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.orders_id_seq OWNED BY public.orders.id;


--
-- Name: part_stock_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.part_stock_log (
    id integer NOT NULL,
    part_id integer NOT NULL,
    change_qty integer NOT NULL,
    after_qty integer NOT NULL,
    change_type character varying(20) NOT NULL,
    related_order_id integer,
    operator character varying(100),
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT part_stock_log_change_type_check CHECK (((change_type)::text = ANY ((ARRAY['in'::character varying, 'out'::character varying, 'adjust'::character varying])::text[])))
);


--
-- Name: part_stock_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.part_stock_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: part_stock_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.part_stock_log_id_seq OWNED BY public.part_stock_log.id;


--
-- Name: part_usage; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.part_usage (
    id integer NOT NULL,
    order_id integer NOT NULL,
    part_id integer NOT NULL,
    quantity integer DEFAULT 1 NOT NULL,
    unit_price numeric(10,2),
    total_price numeric(10,2) GENERATED ALWAYS AS (((quantity)::numeric * unit_price)) STORED,
    used_by_staff_id integer,
    notes text,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: part_usage_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.part_usage_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: part_usage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.part_usage_id_seq OWNED BY public.part_usage.id;


--
-- Name: parts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parts (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    part_code character varying(50),
    category character varying(100),
    description text,
    unit character varying(20) DEFAULT '个'::character varying,
    stock integer DEFAULT 0 NOT NULL,
    min_stock integer DEFAULT 5 NOT NULL,
    cost_price numeric(10,2) DEFAULT 0,
    selling_price numeric(10,2) DEFAULT 0,
    brand_id integer,
    model_id integer,
    is_active boolean DEFAULT true,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT chk_parts_stock_non_negative CHECK ((stock >= 0))
);


--
-- Name: parts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.parts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: parts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.parts_id_seq OWNED BY public.parts.id;


--
-- Name: price_overrides; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.price_overrides (
    id integer NOT NULL,
    product_type_id integer,
    brand_id integer,
    model_id integer,
    service_type_id integer,
    price real NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    category text,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: price_overrides_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.price_overrides_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: price_overrides_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.price_overrides_id_seq OWNED BY public.price_overrides.id;


--
-- Name: product_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product_types (
    id integer NOT NULL,
    name text NOT NULL,
    sort_order integer DEFAULT 0,
    is_active integer DEFAULT 1,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    categories text[],
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: product_types_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_types_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_types_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_types_id_seq OWNED BY public.product_types.id;


--
-- Name: service_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.service_items (
    id integer NOT NULL,
    product_type_id integer,
    name text NOT NULL,
    description text DEFAULT ''::text,
    is_required integer DEFAULT 1,
    sort_order integer DEFAULT 0,
    is_active integer DEFAULT 1,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: service_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.service_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: service_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.service_items_id_seq OWNED BY public.service_items.id;


--
-- Name: service_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.service_types (
    id integer NOT NULL,
    product_type_id integer,
    name text NOT NULL,
    description text DEFAULT ''::text,
    base_price real DEFAULT 0,
    sort_order integer DEFAULT 0,
    is_active integer DEFAULT 1,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    brand_id integer,
    category text DEFAULT ''::text,
    category_id integer,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: service_types_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.service_types_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: service_types_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.service_types_id_seq OWNED BY public.service_types.id;


--
-- Name: special_service_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.special_service_records (
    id integer NOT NULL,
    order_id integer,
    order_item_id integer,
    special_service_id integer,
    name text DEFAULT ''::text,
    description text DEFAULT ''::text,
    price real DEFAULT 0,
    status text DEFAULT 'pending'::text,
    staff_photos text DEFAULT '[]'::text,
    staff_note text DEFAULT ''::text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    confirmed_at timestamp without time zone,
    paid_at timestamp without time zone,
    quantity integer DEFAULT 1,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: special_service_records_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.special_service_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: special_service_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.special_service_records_id_seq OWNED BY public.special_service_records.id;


--
-- Name: special_services; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.special_services (
    id integer NOT NULL,
    name text NOT NULL,
    description text DEFAULT ''::text,
    preset_price real DEFAULT 0,
    is_active integer DEFAULT 1,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: special_services_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.special_services_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: special_services_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.special_services_id_seq OWNED BY public.special_services.id;


--
-- Name: staff; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.staff (
    id integer NOT NULL,
    username text NOT NULL,
    password_hash text NOT NULL,
    full_name text DEFAULT ''::text,
    role text DEFAULT 'technician'::text,
    is_active integer DEFAULT 1,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: staff_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.staff_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: staff_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.staff_id_seq OWNED BY public.staff.id;


--
-- Name: staff_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.staff_tokens (
    id integer NOT NULL,
    staff_id integer NOT NULL,
    token text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamp with time zone,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: staff_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.staff_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: staff_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.staff_tokens_id_seq OWNED BY public.staff_tokens.id;


--
-- Name: status_change_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.status_change_log (
    id bigint NOT NULL,
    order_id integer NOT NULL,
    field text NOT NULL,
    old_value text,
    new_value text,
    changed_by text,
    changed_via text,
    changed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT status_change_log_field_check CHECK ((field = ANY (ARRAY['status'::text, 'payment_status'::text, 'assigned_staff'::text, 'urgent_service'::text])))
);


--
-- Name: status_change_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.status_change_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: status_change_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.status_change_log_id_seq OWNED BY public.status_change_log.id;


--
-- Name: tracking_nodes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tracking_nodes (
    id integer NOT NULL,
    order_id integer,
    node_code text NOT NULL,
    node_name text NOT NULL,
    description text DEFAULT ''::text,
    staff_id integer,
    staff_name text DEFAULT ''::text,
    operate_time timestamp without time zone,
    operate_note text DEFAULT ''::text,
    photos text DEFAULT '[]'::text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT chk_tracking_nodes_node_code CHECK ((node_code = ANY (ARRAY['created'::text, 'received'::text, 'inspect'::text, 'repair'::text, 'qc'::text, 'shipped'::text, 'completed'::text, 'payment_update'::text, 'special_service'::text, 'special_update'::text])))
);


--
-- Name: tracking_nodes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tracking_nodes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tracking_nodes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tracking_nodes_id_seq OWNED BY public.tracking_nodes.id;


--
-- Name: brands id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.brands ALTER COLUMN id SET DEFAULT nextval('public.brands_id_seq'::regclass);


--
-- Name: categories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories ALTER COLUMN id SET DEFAULT nextval('public.categories_id_seq'::regclass);


--
-- Name: customer_addresses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_addresses ALTER COLUMN id SET DEFAULT nextval('public.customer_addresses_id_seq'::regclass);


--
-- Name: customer_tokens id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_tokens ALTER COLUMN id SET DEFAULT nextval('public.customer_tokens_id_seq'::regclass);


--
-- Name: customers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers ALTER COLUMN id SET DEFAULT nextval('public.customers_id_seq'::regclass);


--
-- Name: equipment_inspection_data id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipment_inspection_data ALTER COLUMN id SET DEFAULT nextval('public.equipment_inspection_data_id_seq'::regclass);


--
-- Name: maintenance_reminders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_reminders ALTER COLUMN id SET DEFAULT nextval('public.maintenance_reminders_id_seq'::regclass);


--
-- Name: model_categories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_categories ALTER COLUMN id SET DEFAULT nextval('public.model_categories_id_seq'::regclass);


--
-- Name: models id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.models ALTER COLUMN id SET DEFAULT nextval('public.models_id_seq'::regclass);


--
-- Name: order_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items ALTER COLUMN id SET DEFAULT nextval('public.order_items_id_seq'::regclass);


--
-- Name: order_status_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_status_log ALTER COLUMN id SET DEFAULT nextval('public.order_status_log_id_seq'::regclass);


--
-- Name: orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders ALTER COLUMN id SET DEFAULT nextval('public.orders_id_seq'::regclass);


--
-- Name: part_stock_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.part_stock_log ALTER COLUMN id SET DEFAULT nextval('public.part_stock_log_id_seq'::regclass);


--
-- Name: part_usage id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.part_usage ALTER COLUMN id SET DEFAULT nextval('public.part_usage_id_seq'::regclass);


--
-- Name: parts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parts ALTER COLUMN id SET DEFAULT nextval('public.parts_id_seq'::regclass);


--
-- Name: price_overrides id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.price_overrides ALTER COLUMN id SET DEFAULT nextval('public.price_overrides_id_seq'::regclass);


--
-- Name: product_types id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_types ALTER COLUMN id SET DEFAULT nextval('public.product_types_id_seq'::regclass);


--
-- Name: service_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_items ALTER COLUMN id SET DEFAULT nextval('public.service_items_id_seq'::regclass);


--
-- Name: service_types id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_types ALTER COLUMN id SET DEFAULT nextval('public.service_types_id_seq'::regclass);


--
-- Name: special_service_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.special_service_records ALTER COLUMN id SET DEFAULT nextval('public.special_service_records_id_seq'::regclass);


--
-- Name: special_services id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.special_services ALTER COLUMN id SET DEFAULT nextval('public.special_services_id_seq'::regclass);


--
-- Name: staff id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff ALTER COLUMN id SET DEFAULT nextval('public.staff_id_seq'::regclass);


--
-- Name: staff_tokens id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff_tokens ALTER COLUMN id SET DEFAULT nextval('public.staff_tokens_id_seq'::regclass);


--
-- Name: status_change_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.status_change_log ALTER COLUMN id SET DEFAULT nextval('public.status_change_log_id_seq'::regclass);


--
-- Name: tracking_nodes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tracking_nodes ALTER COLUMN id SET DEFAULT nextval('public.tracking_nodes_id_seq'::regclass);


--
-- Name: brands brands_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.brands
    ADD CONSTRAINT brands_pkey PRIMARY KEY (id);


--
-- Name: categories categories_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_name_key UNIQUE (name);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: customer_addresses customer_addresses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_addresses
    ADD CONSTRAINT customer_addresses_pkey PRIMARY KEY (id);


--
-- Name: customer_tokens customer_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_tokens
    ADD CONSTRAINT customer_tokens_pkey PRIMARY KEY (id);


--
-- Name: customer_tokens customer_tokens_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_tokens
    ADD CONSTRAINT customer_tokens_token_key UNIQUE (token);


--
-- Name: customers customers_openid_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_openid_key UNIQUE (openid);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);


--
-- Name: equipment_inspection_data equipment_inspection_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipment_inspection_data
    ADD CONSTRAINT equipment_inspection_data_pkey PRIMARY KEY (id);


--
-- Name: maintenance_reminders maintenance_reminders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_reminders
    ADD CONSTRAINT maintenance_reminders_pkey PRIMARY KEY (id);


--
-- Name: model_categories model_categories_model_id_category_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_categories
    ADD CONSTRAINT model_categories_model_id_category_id_key UNIQUE (model_id, category_id);


--
-- Name: model_categories model_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_categories
    ADD CONSTRAINT model_categories_pkey PRIMARY KEY (id);


--
-- Name: models models_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.models
    ADD CONSTRAINT models_pkey PRIMARY KEY (id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (id);


--
-- Name: order_status_log order_status_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_status_log
    ADD CONSTRAINT order_status_log_pkey PRIMARY KEY (id);


--
-- Name: orders orders_order_no_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_order_no_key UNIQUE (order_no);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: part_stock_log part_stock_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.part_stock_log
    ADD CONSTRAINT part_stock_log_pkey PRIMARY KEY (id);


--
-- Name: part_usage part_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.part_usage
    ADD CONSTRAINT part_usage_pkey PRIMARY KEY (id);


--
-- Name: parts parts_part_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parts
    ADD CONSTRAINT parts_part_code_key UNIQUE (part_code);


--
-- Name: parts parts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parts
    ADD CONSTRAINT parts_pkey PRIMARY KEY (id);


--
-- Name: price_overrides price_overrides_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.price_overrides
    ADD CONSTRAINT price_overrides_pkey PRIMARY KEY (id);


--
-- Name: price_overrides price_overrides_product_type_id_brand_id_model_id_service_t_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.price_overrides
    ADD CONSTRAINT price_overrides_product_type_id_brand_id_model_id_service_t_key UNIQUE (product_type_id, brand_id, model_id, service_type_id);


--
-- Name: product_types product_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_types
    ADD CONSTRAINT product_types_pkey PRIMARY KEY (id);


--
-- Name: service_items service_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_items
    ADD CONSTRAINT service_items_pkey PRIMARY KEY (id);


--
-- Name: service_types service_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_types
    ADD CONSTRAINT service_types_pkey PRIMARY KEY (id);


--
-- Name: special_service_records special_service_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.special_service_records
    ADD CONSTRAINT special_service_records_pkey PRIMARY KEY (id);


--
-- Name: special_services special_services_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.special_services
    ADD CONSTRAINT special_services_pkey PRIMARY KEY (id);


--
-- Name: staff staff_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_pkey PRIMARY KEY (id);


--
-- Name: staff_tokens staff_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff_tokens
    ADD CONSTRAINT staff_tokens_pkey PRIMARY KEY (id);


--
-- Name: staff_tokens staff_tokens_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff_tokens
    ADD CONSTRAINT staff_tokens_token_key UNIQUE (token);


--
-- Name: staff staff_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_username_key UNIQUE (username);


--
-- Name: status_change_log status_change_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.status_change_log
    ADD CONSTRAINT status_change_log_pkey PRIMARY KEY (id);


--
-- Name: tracking_nodes tracking_nodes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tracking_nodes
    ADD CONSTRAINT tracking_nodes_pkey PRIMARY KEY (id);


--
-- Name: idx_brand_ptype; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_brand_ptype ON public.brands USING btree (product_type_id);


--
-- Name: idx_customer_addresses_cid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_customer_addresses_cid ON public.customer_addresses USING btree (customer_id);


--
-- Name: idx_customer_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_customer_token ON public.customer_tokens USING btree (customer_id);


--
-- Name: idx_customer_tokens_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_customer_tokens_expires ON public.customer_tokens USING btree (expires_at);


--
-- Name: idx_customer_tokens_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_customer_tokens_token ON public.customer_tokens USING btree (token);


--
-- Name: idx_customers_dealer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_customers_dealer ON public.customers USING btree (is_dealer);


--
-- Name: idx_customers_openid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_customers_openid ON public.customers USING btree (openid);


--
-- Name: idx_customers_phone; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_customers_phone ON public.customers USING btree (phone);


--
-- Name: idx_equipment_inspection_item; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_equipment_inspection_item ON public.equipment_inspection_data USING btree (order_item_id);


--
-- Name: idx_equipment_inspection_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_equipment_inspection_order ON public.equipment_inspection_data USING btree (order_id);


--
-- Name: idx_equipment_inspection_order_item; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_equipment_inspection_order_item ON public.equipment_inspection_data USING btree (order_item_id);


--
-- Name: idx_model_brand; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_model_brand ON public.models USING btree (brand_id);


--
-- Name: idx_model_categories_category_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_model_categories_category_id ON public.model_categories USING btree (category_id);


--
-- Name: idx_model_categories_model_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_model_categories_model_id ON public.model_categories USING btree (model_id);


--
-- Name: idx_order_items_brand; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_order_items_brand ON public.order_items USING btree (brand_id);


--
-- Name: idx_order_items_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_order_items_model ON public.order_items USING btree (model_id);


--
-- Name: idx_order_items_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_order_items_order ON public.order_items USING btree (order_id);


--
-- Name: idx_order_items_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_order_items_order_id ON public.order_items USING btree (order_id);


--
-- Name: idx_order_items_product_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_order_items_product_type ON public.order_items USING btree (product_type_id);


--
-- Name: idx_order_items_service; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_order_items_service ON public.order_items USING btree (service_type_id);


--
-- Name: idx_order_items_service_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_order_items_service_type ON public.order_items USING btree (service_type_id);


--
-- Name: idx_order_status_log_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_order_status_log_order ON public.order_status_log USING btree (order_id);


--
-- Name: idx_orders_assigned_staff_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_orders_assigned_staff_id ON public.orders USING btree (assigned_staff_id);


--
-- Name: idx_orders_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_orders_created ON public.orders USING btree (created_at);


--
-- Name: idx_orders_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_orders_created_at ON public.orders USING btree (created_at);


--
-- Name: idx_orders_customer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_orders_customer ON public.orders USING btree (customer_id);


--
-- Name: idx_orders_customer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_orders_customer_id ON public.orders USING btree (customer_id);


--
-- Name: idx_orders_customer_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_orders_customer_status ON public.orders USING btree (customer_id, status);


--
-- Name: idx_orders_order_no; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_orders_order_no ON public.orders USING btree (order_no);


--
-- Name: idx_orders_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_orders_status ON public.orders USING btree (status);


--
-- Name: idx_orders_status_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_orders_status_created_at ON public.orders USING btree (status, created_at);


--
-- Name: idx_orders_urgent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_orders_urgent ON public.orders USING btree (urgent_service);


--
-- Name: idx_part_stock_log_part_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_part_stock_log_part_id ON public.part_stock_log USING btree (part_id);


--
-- Name: idx_part_usage_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_part_usage_order_id ON public.part_usage USING btree (order_id);


--
-- Name: idx_parts_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parts_category ON public.parts USING btree (category);


--
-- Name: idx_service_item_ptype; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_service_item_ptype ON public.service_items USING btree (product_type_id);


--
-- Name: idx_service_type_ptype; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_service_type_ptype ON public.service_types USING btree (product_type_id);


--
-- Name: idx_special_service_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_special_service_order_id ON public.special_service_records USING btree (order_id);


--
-- Name: idx_special_service_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_special_service_status ON public.special_service_records USING btree (status);


--
-- Name: idx_staff_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_staff_token ON public.staff_tokens USING btree (staff_id);


--
-- Name: idx_staff_tokens_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_staff_tokens_token ON public.staff_tokens USING btree (token);


--
-- Name: idx_staff_username; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_staff_username ON public.staff USING btree (username);


--
-- Name: idx_tracking_nodes_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tracking_nodes_created_at ON public.tracking_nodes USING btree (created_at);


--
-- Name: idx_tracking_nodes_order_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tracking_nodes_order_code ON public.tracking_nodes USING btree (order_id, node_code);


--
-- Name: idx_tracking_nodes_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tracking_nodes_order_id ON public.tracking_nodes USING btree (order_id);


--
-- Name: idx_tracking_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tracking_order ON public.tracking_nodes USING btree (order_id);


--
-- Name: brands trg_brands_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_brands_updated_at BEFORE UPDATE ON public.brands FOR EACH ROW EXECUTE FUNCTION public.set_brands_updated_at();


--
-- Name: categories trg_categories_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_categories_updated_at BEFORE UPDATE ON public.categories FOR EACH ROW EXECUTE FUNCTION public.set_categories_updated_at();


--
-- Name: customer_addresses trg_customer_addresses_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_customer_addresses_updated_at BEFORE UPDATE ON public.customer_addresses FOR EACH ROW EXECUTE FUNCTION public.set_customer_addresses_updated_at();


--
-- Name: customer_tokens trg_customer_tokens_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_customer_tokens_updated_at BEFORE UPDATE ON public.customer_tokens FOR EACH ROW EXECUTE FUNCTION public.set_customer_tokens_updated_at();


--
-- Name: model_categories trg_model_categories_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_model_categories_updated_at BEFORE UPDATE ON public.model_categories FOR EACH ROW EXECUTE FUNCTION public.set_model_categories_updated_at();


--
-- Name: models trg_models_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_models_updated_at BEFORE UPDATE ON public.models FOR EACH ROW EXECUTE FUNCTION public.set_models_updated_at();


--
-- Name: order_items trg_order_items_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_order_items_updated_at BEFORE UPDATE ON public.order_items FOR EACH ROW EXECUTE FUNCTION public.set_order_items_updated_at();


--
-- Name: orders trg_order_status_change; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_order_status_change AFTER UPDATE ON public.orders FOR EACH ROW EXECUTE FUNCTION public.log_order_status_change();


--
-- Name: parts trg_parts_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_parts_updated_at BEFORE UPDATE ON public.parts FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: price_overrides trg_price_overrides_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_price_overrides_updated_at BEFORE UPDATE ON public.price_overrides FOR EACH ROW EXECUTE FUNCTION public.set_price_overrides_updated_at();


--
-- Name: product_types trg_product_types_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_product_types_updated_at BEFORE UPDATE ON public.product_types FOR EACH ROW EXECUTE FUNCTION public.set_product_types_updated_at();


--
-- Name: service_items trg_service_items_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_service_items_updated_at BEFORE UPDATE ON public.service_items FOR EACH ROW EXECUTE FUNCTION public.set_service_items_updated_at();


--
-- Name: service_types trg_service_types_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_service_types_updated_at BEFORE UPDATE ON public.service_types FOR EACH ROW EXECUTE FUNCTION public.set_service_types_updated_at();


--
-- Name: special_service_records trg_special_service_records_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_special_service_records_updated_at BEFORE UPDATE ON public.special_service_records FOR EACH ROW EXECUTE FUNCTION public.set_special_service_records_updated_at();


--
-- Name: special_services trg_special_services_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_special_services_updated_at BEFORE UPDATE ON public.special_services FOR EACH ROW EXECUTE FUNCTION public.set_special_services_updated_at();


--
-- Name: staff_tokens trg_staff_tokens_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_staff_tokens_updated_at BEFORE UPDATE ON public.staff_tokens FOR EACH ROW EXECUTE FUNCTION public.set_staff_tokens_updated_at();


--
-- Name: staff trg_staff_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_staff_updated_at BEFORE UPDATE ON public.staff FOR EACH ROW EXECUTE FUNCTION public.set_staff_updated_at();


--
-- Name: tracking_nodes trg_tracking_nodes_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_tracking_nodes_updated_at BEFORE UPDATE ON public.tracking_nodes FOR EACH ROW EXECUTE FUNCTION public.set_tracking_nodes_updated_at();


--
-- Name: customer_addresses customer_addresses_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_addresses
    ADD CONSTRAINT customer_addresses_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE CASCADE;


--
-- Name: equipment_inspection_data equipment_inspection_data_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipment_inspection_data
    ADD CONSTRAINT equipment_inspection_data_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE CASCADE;


--
-- Name: equipment_inspection_data equipment_inspection_data_order_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipment_inspection_data
    ADD CONSTRAINT equipment_inspection_data_order_item_id_fkey FOREIGN KEY (order_item_id) REFERENCES public.order_items(id) ON DELETE CASCADE;


--
-- Name: equipment_inspection_data equipment_inspection_data_staff_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipment_inspection_data
    ADD CONSTRAINT equipment_inspection_data_staff_id_fkey FOREIGN KEY (staff_id) REFERENCES public.staff(id);


--
-- Name: customer_tokens fk_customer_tokens_customer; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_tokens
    ADD CONSTRAINT fk_customer_tokens_customer FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE CASCADE;


--
-- Name: order_items fk_order_items_brand; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT fk_order_items_brand FOREIGN KEY (brand_id) REFERENCES public.brands(id) ON DELETE CASCADE;


--
-- Name: order_items fk_order_items_model; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT fk_order_items_model FOREIGN KEY (model_id) REFERENCES public.models(id) ON DELETE CASCADE;


--
-- Name: order_items fk_order_items_order; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE CASCADE;


--
-- Name: order_items fk_order_items_product_type; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT fk_order_items_product_type FOREIGN KEY (product_type_id) REFERENCES public.product_types(id) ON DELETE CASCADE;


--
-- Name: order_items fk_order_items_service_type; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT fk_order_items_service_type FOREIGN KEY (service_type_id) REFERENCES public.service_types(id) ON DELETE CASCADE;


--
-- Name: orders fk_orders_customer; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE SET NULL;


--
-- Name: price_overrides fk_price_overrides_brand; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.price_overrides
    ADD CONSTRAINT fk_price_overrides_brand FOREIGN KEY (brand_id) REFERENCES public.brands(id) ON DELETE CASCADE;


--
-- Name: price_overrides fk_price_overrides_model; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.price_overrides
    ADD CONSTRAINT fk_price_overrides_model FOREIGN KEY (model_id) REFERENCES public.models(id) ON DELETE CASCADE;


--
-- Name: price_overrides fk_price_overrides_product_type; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.price_overrides
    ADD CONSTRAINT fk_price_overrides_product_type FOREIGN KEY (product_type_id) REFERENCES public.product_types(id) ON DELETE CASCADE;


--
-- Name: price_overrides fk_price_overrides_service_type; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.price_overrides
    ADD CONSTRAINT fk_price_overrides_service_type FOREIGN KEY (service_type_id) REFERENCES public.service_types(id) ON DELETE CASCADE;


--
-- Name: special_service_records fk_ssr_order; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.special_service_records
    ADD CONSTRAINT fk_ssr_order FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE CASCADE;


--
-- Name: special_service_records fk_ssr_order_item; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.special_service_records
    ADD CONSTRAINT fk_ssr_order_item FOREIGN KEY (order_item_id) REFERENCES public.order_items(id) ON DELETE CASCADE;


--
-- Name: staff_tokens fk_staff_tokens_staff; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff_tokens
    ADD CONSTRAINT fk_staff_tokens_staff FOREIGN KEY (staff_id) REFERENCES public.staff(id) ON DELETE CASCADE;


--
-- Name: tracking_nodes fk_tracking_nodes_order; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tracking_nodes
    ADD CONSTRAINT fk_tracking_nodes_order FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE CASCADE;


--
-- Name: maintenance_reminders maintenance_reminders_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_reminders
    ADD CONSTRAINT maintenance_reminders_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE CASCADE;


--
-- Name: maintenance_reminders maintenance_reminders_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_reminders
    ADD CONSTRAINT maintenance_reminders_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE CASCADE;


--
-- Name: model_categories model_categories_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_categories
    ADD CONSTRAINT model_categories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id) ON DELETE CASCADE;


--
-- Name: model_categories model_categories_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_categories
    ADD CONSTRAINT model_categories_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.models(id) ON DELETE CASCADE;


--
-- Name: order_status_log order_status_log_changed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_status_log
    ADD CONSTRAINT order_status_log_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES public.staff(id);


--
-- Name: order_status_log order_status_log_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_status_log
    ADD CONSTRAINT order_status_log_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: part_stock_log part_stock_log_part_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.part_stock_log
    ADD CONSTRAINT part_stock_log_part_id_fkey FOREIGN KEY (part_id) REFERENCES public.parts(id) ON DELETE CASCADE;


--
-- Name: part_usage part_usage_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.part_usage
    ADD CONSTRAINT part_usage_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE CASCADE;


--
-- Name: part_usage part_usage_part_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.part_usage
    ADD CONSTRAINT part_usage_part_id_fkey FOREIGN KEY (part_id) REFERENCES public.parts(id) ON DELETE RESTRICT;


--
-- Name: part_usage part_usage_used_by_staff_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.part_usage
    ADD CONSTRAINT part_usage_used_by_staff_id_fkey FOREIGN KEY (used_by_staff_id) REFERENCES public.staff(id);


--
-- Name: parts parts_brand_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parts
    ADD CONSTRAINT parts_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.brands(id) ON DELETE SET NULL;


--
-- Name: parts parts_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parts
    ADD CONSTRAINT parts_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.models(id) ON DELETE SET NULL;


--
-- Name: service_types service_types_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_types
    ADD CONSTRAINT service_types_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id);


--
-- Name: status_change_log status_change_log_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.status_change_log
    ADD CONSTRAINT status_change_log_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 96moxelK9vfLm1EFgoc9R9oSMHbGcM84UmusD1IHi8aGqu4gIlZ4DmjEU2unPXY

