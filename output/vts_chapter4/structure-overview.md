# Visa Token Service - Structure Overview

**Document Type**: Unknown  
**Converted**: 2025-08-26T17:12:14.645904  
**Source**: VTS_chapter4.pdf  
**Processing Method**: Modular PDF Converter  

## Document Statistics

- **Pages**: 15
- **Sections**: 5
- **Images**: 0
- **Tables**: 0
- **Total Characters**: 21,530

## Table of Contents

1. [Section 1 (Pages 1-3)](#section-1) (content, 835 tokens)\n2. [Section 2 (Pages 4-6)](#section-2) (content, 1100 tokens)\n3. [Section 3 (Pages 7-9)](#section-3) (content, 1167 tokens)\n4. [Section 4 (Pages 10-12)](#section-4) (content, 1152 tokens)\n5. [Section 5 (Pages 13-15)](#section-5) (content, 992 tokens)\n\n---\n\n## 1. Section 1 (Pages 1-3) {#section-1}\n\n**Section Type**: content  \n**Token Count**: 835  \n**Level**: 1  \n**File**: `sections/01-Section-1-Pages-1-3.md`  \n\n**Preview**: Chapter 4
Encrypted Payload Data 
Structures
Cardholder Information
Field
Description
primaryAccountNumber
(Required) Primary account number (PAN) of the card that is being 
tokenized.
Format: String;...\n\n[📖 Read Full Section](sections/01-Section-1-Pages-1-3.md)\n\n---\n\n## 2. Section 2 (Pages 4-6) {#section-2}\n\n**Section Type**: content  \n**Token Count**: 1100  \n**Level**: 1  \n**File**: `sections/02-Section-2-Pages-4-6.md`  \n\n**Preview**: Token Information
Field
Description
token
(Conditional) The account number associated with a token. This is a 
required field in the following APIs:
l
Token Create Notification
l
Token Notification
Fo...\n\n[📖 Read Full Section](sections/02-Section-2-Pages-4-6.md)\n\n---\n\n## 3. Section 3 (Pages 7-9) {#section-3}\n\n**Section Type**: content  \n**Token Count**: 1167  \n**Level**: 1  \n**File**: `sections/03-Section-3-Pages-7-9.md`  \n\n**Preview**: Field
Description
tokenRequestorName
(Conditional) Token requester name. Populated when available in 
the following APIs:
l
Device Token Binding Request
l
Get Cardholder Verification Methods
l
Send Pa...\n\n[📖 Read Full Section](sections/03-Section-3-Pages-7-9.md)\n\n---\n\n## 4. Section 4 (Pages 10-12) {#section-4}\n\n**Section Type**: content  \n**Token Count**: 1152  \n**Level**: 1  \n**File**: `sections/04-Section-4-Pages-10-12.md`  \n\n**Preview**: Field
Description
provisioningAttemptsOnDevice 
In24Hours
Number of provisioning attempts on this device in the past 24 
hours. If the number of attempts exceeds 99, it will stay at 99.
Example: "99"...\n\n[📖 Read Full Section](sections/04-Section-4-Pages-10-12.md)\n\n---\n\n## 5. Section 5 (Pages 13-15) {#section-5}\n\n**Section Type**: content  \n**Token Count**: 992  \n**Level**: 1  \n**File**: `sections/05-Section-5-Pages-13-15.md`  \n\n**Preview**: Field
Description
deviceType
Device type.
Note:  The deviceType field corresponds to Field 125, 
Usage 2 – Dataset ID 01 - Token Device, which is described 
in the VisaNet Authorization-Only Online Me...\n\n[📖 Read Full Section](sections/05-Section-5-Pages-13-15.md)\n\n---\n\n