# Section 4 (Pages 10-12)

**Chunk**: 1 of 1  
**Size**: xlarge (1152 tokens)  
**Section Type**: content  
**Processing Priority**: 4  
**Recommended Model**: gpt-3.5-turbo (4K context)  
**Generated**: 2025-08-26T17:12:14.642885

---

## Processing Guidance

- Optimized for Claude-2 - ideal for comprehensive analysis

---

Field
Description
provisioningAttemptsOnDevice 
In24Hours
Number of provisioning attempts on this device in the past 24 
hours. If the number of attempts exceeds 99, it will stay at 99.
Example: "99"
Format: String; max length 2 characters.
distinctCardholderNames
Number of distinct cardholder names used in provisioning from 
this device.
Example: "99"
Format: String; max length 2 characters.
deviceCountry
Country of device at time of provisioning.
Example: US
Format: String; ISO 3166-1, alpha-2; max length 2 characters.
walletAccountCountry
Country of account-holder.
Example: US
Format: String; ISO 3166-1, alpha-2; max length 2 characters.
suspendedCardsInAccount
Number of cards suspended in the account. If the number of days 
exceeds 99, it will stay at 99.
Example: "99"
Format: String; max length 2 characters.
daysSinceLastAccountActivity
Number of days since the last activity on account. If the number of 
days exceeds 9999, it will stay at 9999.
Example: "9999"
Format: String; max length 4 characters.
numberOfTransactionsInLast 
12months
Number of transactions on this account in the last 12 months. If 
the number of transaction exceeds 9999, it will stay at 9999.
Example: "9999"
Format: String; max length 4 characters.
numberOfActiveTokens
Number of active tokens on this account. If the number of tokens 
exceeds 99, it will stay at 99
Example: "99"
Format: String; max length 2 characters.
deviceWithActiveTokens
Number of devices for this user with the same token. If the 
number of tokens exceeds 99, it will stay at 99
Example: "99"
Format: String; max length 2 characters.
Visa Token Service – Issuer API Specifications (JSON)
Encrypted Payload Data Structures
27 March 2025
Visa Confidential
65
\n\nField
Description
activeTokensOnAllDeviceFor 
Account
Number of active tokens for this user, across all devices. If the 
number of tokens exceeds 9999, it will stay at 9999.
Example: "9999"
Format: String; max length 4 characters.
visaTokenScore
Value indicating the degree of risk associated with the token. 
Numeric value is 00 through 99. A value of 00 indicates no score 
provided by Visa.
Format: String; max length 2 characters.
visaTokenDecisioning
Results from the token provisioning service.
Format: It is one of the following values:
l
00 – Provision and activate
l
05 – Do not provision
l
85 – Provision in inactive state (requires further consumer 
authentication prior to activation)
riskAssessmentScore
Values are 0 through 99. A higher value indicates a higher risk. This 
is calculated by the AA Risk Engine, based on the PAN’s transaction 
pattern (long term and short term).
Format: String; max length 2 characters.
issuerSpecialConditionCodes
Supported for issuers participating in 0100 TAR. The issuer can 
send values for this element in the 0100 TAR response.
l
If the issuer sends a value in the 0100 TAR, it will be sent in this 
element of the Get CVM.
l
If no value is sent in 0100 TAR or if the issuer does not 
participate in TAR, this element will not be present.
Format: String; max length 100 characters.
Visa Token Service – Issuer API Specifications (JSON)
Encrypted Payload Data Structures
27 March 2025
Visa Confidential
66
\n\nDevice Information
Field
Description
deviceID
For Secure Element (SE) wallet providers, this value will be the SE 
ID in hex binary characters transformed to a 48-character string.
For Host Card Emulation (HCE) wallet providers, this field will be 
the Device ID as determined by the digital wallet provider (DWP). 
All alphanumeric and special characters are allowed for HCE DWPs.
Secure Element (SE) ID represents the device ID.
l
For SE DWPs, this value will be the SE ID in hex binary characters 
transformed to a 48-character string.
l
For CBP DWPs, this field will be the device ID as determined by 
the DWP. All alphanumeric and special characters are allowed 
for CBP DWPs.
For Card-on-File (COF) wallets, this value will not be present.
For the initial Check Eligibility request on PAN enrollment, this 
value may not be available, however Visa will send this value if it is 
available.
Format: String; max length 48 characters.
deviceLanguageCode
This value is any ISO 639 Version 3 Language Code, for example, 
eng (English). This language code will be used by the issuer and 
Visa to retrieve the Terms and Conditions (T&C). If T&Cs are not 
found for the Language Code in the request, the T&Cs will return 
the default :anguage Code of eng (English).
Format: String; ISO-639 Version 3 Language Code, max length 3 
characters.
Visa Token Service – Issuer API Specifications (JSON)
Encrypted Payload Data Structures
27 March 2025
Visa Confidential
67
