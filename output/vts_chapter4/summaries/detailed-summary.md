---
title: Detailed Summary
type: detailed
generated: 2025-08-26T17:12:14.627390
token_count: 598
---

# Detailed Summary

This Api Documentation follows a General Documentation structure with 5 main sections.

## Section Breakdown

### 1. Section 1 (Pages 1-3)

Chapter 4
Encrypted Payload Data 
Structures
Cardholder Information
Field
Description
primaryAccountNumber
(Required) Primary account number (PAN) of the card that is being 
tokenized Format: String; max length 19 characters

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
SUSPEN...

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
Format: String; max length 100 characters This is a required field in the following APIs:
l
Approve Provisioning
l
Approve Provisioning Stand-In Notification
l
Token Create Notification
Format: It is one of the following values:
l
true — Indicates that the token (e-Commerce Enabler, or Card-
on-File) is for an autofill use case

### 4. Section 4 (Pages 10-12)

Field
Description
provisioningAttemptsOnDevice 
In24Hours
Number of provisioning attempts on this device in the past 24 
hours If the number of attempts exceeds 99, it will stay at 99 Example: "99"
Format: String; max length 2 characters

### 5. Section 5 (Pages 13-15)

Field
Description
deviceType
Device type Note:  The deviceType field corresponds to Field 125, 
Usage 2 – Dataset ID 01 - Token Device, which is described 
in the VisaNet Authorization-Only Online Messages – Technical 
Specifications Example: My Work Phone
Format: String; Base64URL-encoded; UTF-8; max length 128 
characters

