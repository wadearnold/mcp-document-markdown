---
title: Complete Summary
type: complete
generated: 2025-08-26T17:12:14.627533
token_count: 1500
---

# Complete Summary

## Document Analysis

**Type**: Api Documentation
**Technical Depth**: Moderately Technical
**Main Themes**: API Integration, Authentication, Data Management, Security
**Total Sections**: 5

## Complete Section Analysis

### 1. Section 1 (Pages 1-3)

Chapter 4
Encrypted Payload Data 
Structures
Cardholder Information
Field
Description
primaryAccountNumber
(Required) Primary account number (PAN) of the card that is being 
tokenized Format: String; max length 19 characters cvv2
(Optional) Value associated with the PAN on the card Example: "year": "2024"
Format: String; numeric; length 4 digits Visa Token Service – Issuer API Specifications (JSON)
Encrypted Payload Data Structures
27 March 2025
Visa Confidential
58 This is a required field for Secure Remote Commerce and in the 
following APIs:
l
Approve Provisioning
l
Token Create Notification
Format: An Expiration Date structure It is required for Secure Remote Commerce Example: NY
Format: String; ISO 3166-2; max length 2 characters

**Key Examples:**
- Example: NY...
- Example: US...

### 2. Section 2 (Pages 4-6)

Token Information
Field
Description
token
(Conditional) The account number associated with a token This is a 
required field in the following APIs:
l
Token Create Notification
l
Token Notification
Format: String; max length 19 characters tokenType
(Conditional) This is a required field in the following APIs:
l
Approve Provisioning
l
Approve Provisioning Stand-In Notification
l
Token Create Notification
Format: It is one of the following values:
l
SECURE_ELEMENT
l
HCE
l
CARD_ON_FILE
l
ECOMMERCE
l
QRC
tokenStatus
(Conditional) This is a required field in the following APIs:
l
Token Create Notification
l
Token Notification
Format: It is one of the following values:
l
ACTIVE
l
INACTIVE
l
SUSPENDED
l
DEACTIVATED
tokenExpirationDate
(Conditional) The date upon which the token is set to expire It is 
one of the following values:
l
00 ID&V Not Performed
l
10 Card Issuer Account Verification
l
11 Card Issuer Interactive Cardholder Verification - 1 Factor
l
12 Card Issuer Interactive Cardholder Verification - 2 Factor
l
13 Card Issuer Risk Oriented Non-Interactive Cardholder 
Authentication
l
14 Card Issuer Asserted Authentication
Format: String; max length 2 characters Visa Token Service – Issuer API Specifications (JSON)
Encrypted Payload Data Structures
27 March 2025
Visa Confidential
61 This 
field is required in the Token Create Notification API originalTokenRequestorID
(Required) Unique ID assigned to the initiator of the token request

### 3. Section 3 (Pages 7-9)

Field
Description
tokenRequestorName
(Conditional) Token requester name Populated when available in 
the following APIs:
l
Device Token Binding Request
l
Get Cardholder Verification Methods
l
Send Passcode
l
Token Notification
Format: String; max length 100 characters autoFillIndicator
(Conditional) Indicates whether the token is for an autofill use case Example: "999"
Format: String; max length 4 characters Visa Token Service – Issuer API Specifications (JSON)
Encrypted Payload Data Structures
27 March 2025
Visa Confidential
64 This is a required field in the following APIs:
l
Approve Provisioning
l
Approve Provisioning Stand-In Notification
l
Token Create Notification
Format: It is one of the following values:
l
true — Indicates that the token (e-Commerce Enabler, or Card-
on-File) is for an autofill use case May contain separators to indicate major and minor components, 
for example, periods, hyphens, slashes, and other similar 
characters Example: 5
Format: String; max length 2 characters

**Key Examples:**
- Example: 5...
- Example: 5...

### 4. Section 4 (Pages 10-12)

Field
Description
provisioningAttemptsOnDevice 
In24Hours
Number of provisioning attempts on this device in the past 24 
hours If the number of attempts exceeds 99, it will stay at 99 Example: "99"
Format: String; max length 2 characters Format: String; ISO-639 Version 3 Language Code, max length 3 
characters Visa Token Service – Issuer API Specifications (JSON)
Encrypted Payload Data Structures
27 March 2025
Visa Confidential
67 Example: "99"
Format: String; max length 2 characters Example: US
Format: String; ISO 3166-1, alpha-2; max length 2 characters Example: US
Format: String; ISO 3166-1, alpha-2; max length 2 characters

**Key Examples:**
- Example: "99"...
- Example: "99"...

### 5. Section 5 (Pages 13-15)

Field
Description
deviceType
Device type Note:  The deviceType field corresponds to Field 125, 
Usage 2 – Dataset ID 01 - Token Device, which is described 
in the VisaNet Authorization-Only Online Messages – Technical 
Specifications Format: It is one of the following values:
l
UNKNOWN
l
MOBILE_PHONE, which is equivalent to value 01 in Field 125
l
TABLET, which is equivalent to value 02 in Field 125
l
WATCH
l
MOBILEPHONE_OR_TABLET, which is equivalent to value 04 in 
Field 125
l
PC
l
HOUSEHOLD_DEVICE
l
WEARABLE_DEVICE
l
AUTOMOBILE_DEVICE
deviceName
A readable name for the device originalDeviceType
Device type from the original provision This field is populated only 
when performing token-for-token provisioning and can be used 
only in the following APIs:
l
Approve Provisioning
l
Approve Provisioning Stand-In Notification
l
Token Create Notification
Format: It is one of the following values:
l
UNKNOWN
l
MOBILE_PHONE
l
TABLET
l
WATCH
l
MOBILEPHONE_OR_TABLET
l
PC
l
HOUSEHOLD_DEVICE
l
WEARABLE_DEVICE
l
AUTOMOBILE_DEVICE
Visa Token Service – Issuer API Specifications (JSON)
Encrypted Payload Data Structures
27 March 2025
Visa Confidential
70 Example: My Work Phone
Format: String; Base64URL-encoded; UTF-8; max length 128 
characters Example: 4.4.4
Format: String; max length 32 characters Example: KTU84M
Format: String; max length 32 characters

**Key Examples:**
- Example: My Work Phone...
- Example: 4.4.4...

