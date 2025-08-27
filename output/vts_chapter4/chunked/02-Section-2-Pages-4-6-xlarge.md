# Section 2 (Pages 4-6)

**Chunk**: 1 of 1  
**Size**: xlarge (1100 tokens)  
**Section Type**: content  
**Processing Priority**: 4  
**Recommended Model**: gpt-3.5-turbo (4K context)  
**Generated**: 2025-08-26T17:12:14.634126

---

## Processing Guidance

- Optimized for Claude-2 - ideal for comprehensive analysis

---

Token Information
Field
Description
token
(Conditional) The account number associated with a token. This is a 
required field in the following APIs:
l
Token Create Notification
l
Token Notification
Format: String; max length 19 characters.
tokenType
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
(Conditional) The date upon which the token is set to expire. This 
field is required in the Token Create Notification API. It is provided 
in the Token Notification API request if available.
Format: An Expiration Date structure.
Visa Token Service – Issuer API Specifications (JSON)
Encrypted Payload Data Structures
27 March 2025
Visa Confidential
59
\n\nField
Description
tokenAssuranceMethod
(Optional) Method of Issuer ID&V that has taken place at time of 
provisioning, device binding, or cardholder initiated verification. It 
is one of the following values:
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
Format: String; max length 2 characters.
numberOfActiveTokensForPAN
(Optional) Number of device tokens that are currently active for this 
PAN.
Format: Integer; max length 4 digits.
numberOfInactiveTokensForPAN
(Optional) Number of device tokens that are currently inactive 
(device tokens have not been activated) for this PAN.
Format: Integer; max length 4 digits.
numberOfSuspendedTokensForPAN
(Optional) Number of device tokens that were activated, but are 
suspended for payments for this PAN.
Format: Integer; max length 4 digits.
tokenActivationDate
(Optional) System date/timestamp, in GMT, of token activation into 
an active state. For an inactive state, this field is left empty and 
populated only when a token transitions to an active state. If a 
token is suspended, this field is populated with the new date/
timestamp of when an active state resumes.
Format: String; yyyy-MM-ddTHH:mm:ss.SSSZ.
tokenDeactivationDate
(Optional) Date of token deactivation.
Format: String; YYYY-MM-DD.
lastTokenStatusUpdatedTime
(Optional) Date/timestamp, in GMT, of the last token status update.
Format: String; yyyy-MM-ddTHH:mm:ss.SSSZ.
originalToken
(Conditional) Token account number. This field is populated when 
performing token-for-token provisioning only.
Format: String; max length 19 characters.
originalTokenRequestorID
(Required) Unique ID assigned to the initiator of the token request. 
This field is populated when performing token-for-token 
provisioning only.
Format: Numeric; max length 11 digits.
Visa Token Service – Issuer API Specifications (JSON)
Encrypted Payload Data Structures
27 March 2025
Visa Confidential
60
\n\nField
Description
originalTokenReferenceID
(Conditional) Unique ID for the token associated with the PAN. This 
ID can be used in lieu of the token for subsequent calls, such as life 
cycle events. This field is populated when performing token-for-
token provisioning only.
Format: String; max length 32 characters.
originalTokenType
(Conditional) Token type of the original token. This field is 
populated only when performing token for token provisioning and 
can be used only in the following APIs:
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
l
PSEUDO_ACCOUNT
originaltokenAssuranceMethod
(Conditional) Original token assurance method. This field is 
populated when performing token-for-token provisioning only. It is 
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
Format: String; max length 2 characters.
Visa Token Service – Issuer API Specifications (JSON)
Encrypted Payload Data Structures
27 March 2025
Visa Confidential
61
