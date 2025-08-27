# Visa Token Service

## Document Metadata

- **Source**: VTS_chapter4.pdf
- **Pages**: 15
- **Extraction Method**: ULTIMATE
- **Field Count**: 89
- **Sections**: 6

---

## Document Summary

This document contains API field definitions with structured information including:

- **Field Names**: API parameter identifiers
- **Requirements**: Whether fields are Required, Optional, or Conditional
- **Data Types**: Inferred from format specifications and allowed values
- **Descriptions**: Functional explanations of each field
- **Format Specifications**: Expected data formats and constraints
- **Examples**: Sample values for implementation guidance
- **Allowed Values**: Enumerated options where applicable

---

## Table of Contents

1. [Cardholder Information](#cardholder-information) (19 fields)
2. [Token Information](#token-information) (20 fields)
3. [Device Information](#device-information) (27 fields)
4. [Risk Information](#risk-information) (6 fields)
5. [Address](#address) (5 fields)
6. [Other Fields](#other-fields) (12 fields)

---

## Cardholder Information

This section contains 19 field(s) related to cardholder information.

| Field | Type | Required | Description | Format | Example | Values |
|-------|------|----------|-------------|--------|---------|--------|
| `primaryAccountNumber` | number | Required | Primary account number (PAN) of the card that is being tokenized. cvv2 (Optional) Value associated with the PAN on the card. | String; max length 4 characters. |  |  |
| `name` | string | Optional | Full name on the Visa card associated with the enrolled payment instrument. 27 March 2025 Visa Confidential 56 | String; max length 256 characters. |  |  |
| `numberOfActiveTokensForPAN` | number | Optional | Number of device tokens that are currently active for this PAN. | Integer; max length 4 digits. |  |  |
| `numberOfInactiveTokensForPAN` | number | Optional | Number of device tokens that are currently inactive (device tokens have not been activated) for this PAN. | Integer; max length 4 digits. |  |  |
| `numberOfSuspendedTokensForPAN` | number | Optional | Number of device tokens that were activated, but are suspended for payments for this PAN. | Integer; max length 4 digits. |  |  |
| `tokenRequestorName` | enum | Conditional | Token requester name. Populated when available in the following APIs: | String; max length 100 characters. |  | 4 options: `Device Token Binding Request`, `Get Cardholder Verification Methods`... |
| `walletProviderAccountScore` | string |  | The wallet provider account score. Score value is between1 and 5, indicating the confidence level of the account, where 5 indicates the most confidence on the account. | String; max length 2 characters. | 5 |  |
| `accountHolderName` | string |  | Account-holder’s name. | String; max length 64 characters. |  |  |
| `walletProviderPANAge` | datetime |  | Length of time (in days) that a PAN has been on file for a user. | String; max length 4 characters. | "9999" |  |
| `walletAccountHolderCardNameMatch` | string |  | Name of the account-holder and name of cardholder matched. • Y-- Indicates the two names match. • N-- Indicates the two names do not match. | It is one of the following values: |  |  |
| `accountToDeviceBindingAge` | number |  | Number of days this device has been used by this account. If the number of days exceeds 9999, it will stay at 9999. | String; max length 4 characters. | 9999 |  |
| `userAccountAge` | number |  | Number of days since an account for this user has existed (how long have you known this user?). Values are 0 through 9999. | String; max length 4 characters. | "9999" |  |
| `walletAccountAge` | number |  | Number of days since the user created a wallet account or started using a wallet. If the number of days exceeds 256, it will stay at 256. | String; max length 4 characters. | "256" |  |
| `walletAccountEmailAddressAge` | number |  | Number of days since the email address was associated with the account. If the number of days exceeds 999, it will stay at 999. Visa Token Service - Issuer API Specifications (JSON) Encrypted Payload Data Structures 27 March 2025 Visa Confidential 64 | String; max length 4 characters. | "999" |  |
| `distinctCardholderNames` | number |  | Number of distinct cardholder names used in provisioning from this device. | String; max length 2 characters. | "99" |  |
| `walletAccountCountry` | string |  | Country of account-holder. | String; ISO 3166-1, alpha-2; max length 2 characters. | US |  |
| `suspendedCardsInAccount` | number |  | Number of cards suspended in the account. If the number of days exceeds 99, it will stay at 99. | String; max length 2 characters. | "99" |  |
| `daysSinceLastAccountActivity` | number |  | Number of days since the last activity on account. If the number of days exceeds 9999, it will stay at 9999. | String; max length 4 characters. | "9999" |  |
| `deviceName` | string |  | A readable name for the device. Ideally, the customer enters this name. It can be used to identify the device in customer support calls. characters. | String; Base64URL-encoded; UTF-8; max length 128 | My Work Phone |  |

---

## Token Information

This section contains 20 field(s) related to token information.

| Field | Type | Required | Description | Format | Example | Values |
|-------|------|----------|-------------|--------|---------|--------|
| `token` | enum | Conditional | The account number associated with a token. This is a required field in the following APIs: | String; max length 19 characters. |  | `Token Create Notification`, `Token Notification` |
| `tokenType` | string | Conditional | This is a required field in the following APIs: | It is one of the following values: |  | 8 options: `Approve Provisioning`, `Approve Provisioning Stand-In Notification`... |
| `tokenStatus` | string | Conditional | This is a required field in the following APIs: | It is one of the following values: |  | 6 options: `Token Create Notification`, `Token Notification`... |
| `tokenExpirationDate` | datetime | Conditional | The date upon which the token is set to expire. This field is required in the Token Create Notification API. It is provided in the Token Notification API request if available. Visa Token Service - Issuer API Specifications (JSON) Encrypted Payload Data Structures 27 March 2025 Visa Confidential 59 | An Expiration Date structure. |  |  |
| `tokenAssuranceMethod` | enum | Optional | Method of Issuer ID&V that has taken place at time of provisioning, device binding, or cardholder initiated verification. It is one of the following values: |  |  | 5 options: `00 ID&V Not Performed`, `10 Card Issuer Account Verification`... |
| `tokenActivationDate` | datetime | Optional | System date/timestamp, in GMT, of token activation into an active state. For an inactive state, this field is left empty and populated only when a token transitions to an active state. If a token is suspended, this field is populated with the new date/ timestamp of when an active state resumes. | String; yyyy-MM-ddTHH:mm:ss.SSSZ. |  |  |
| `tokenDeactivationDate` | datetime | Optional | Date of token deactivation. | String; YYYY-MM-DD. |  |  |
| `lastTokenStatusUpdatedTime` | datetime | Optional | Date/timestamp, in GMT, of the last token status update. | String; yyyy-MM-ddTHH:mm:ss.SSSZ. |  |  |
| `originalToken` | number | Conditional | Token account number. This field is populated when performing token-for-token provisioning only. | String; max length 19 characters. |  |  |
| `originalTokenRequestorID` | number | Required | Unique ID assigned to the initiator of the token request. This field is populated when performing token-for-token provisioning only. Visa Token Service - Issuer API Specifications (JSON) Encrypted Payload Data Structures 27 March 2025 Visa Confidential 60 | Numeric; max length 11 digits. |  |  |
| `originalTokenReferenceID` | string | Conditional | Unique ID for the token associated with the PAN. This ID can be used in lieu of the token for subsequent calls, such as life cycle events. This field is populated when performing token-for- token provisioning only. | String; max length 32 characters. |  |  |
| `originalTokenType` | string | Conditional | Token type of the original token. This field is populated only when performing token for token provisioning and can be used only in the following APIs: | It is one of the following values: |  | 9 options: `Approve Provisioning`, `Approve Provisioning Stand-In Notification`... |
| `originaltokenAssuranceMethod` | enum | Conditional | Original token assurance method. This field is populated when performing token-for-token provisioning only. It is one of the following values: |  |  | 5 options: `00 ID&V Not Performed`, `10 Card Issuer Account Verification`... |
| `provisioningAttemptsOnDevice` | number |  | In24Hours Number of provisioning attempts on this device in the past 24 hours. If the number of attempts exceeds 99, it will stay at 99. | String; max length 2 characters. | "99" |  |
| `numberOfActiveTokens` | number |  | Number of active tokens on this account. If the number of tokens exceeds 99, it will stay at 99 | String; max length 2 characters. | "99" |  |
| `deviceWithActiveTokens` | number |  | Number of devices for this user with the same token. If the number of tokens exceeds 99, it will stay at 99 Visa Token Service - Issuer API Specifications (JSON) Encrypted Payload Data Structures 27 March 2025 Visa Confidential 65 | String; max length 2 characters. | "99" |  |
| `activeTokensOnAllDeviceFor` | number |  | Account Number of active tokens for this user, across all devices. If the number of tokens exceeds 9999, it will stay at 9999. | String; max length 4 characters. | "9999" |  |
| `visaTokenScore` | number |  | Value indicating the degree of risk associated with the token. Numeric value is 00 through 99. A value of 00 indicates no score provided by Visa. | String; max length 2 characters. |  |  |
| `visaTokenDecisioning` | string |  | Results from the token provisioning service. • 00 - Provision and activate • 05 - Do not provision • 85 - Provision in inactive state (requires further consumer authentication prior to activation) | It is one of the following values: |  |  |
| `tokenProtectionMethod` | string |  | Method of token protection. • SOFTWARE • TRUSTED_EXECUTION_ENVIRONMENT • SECURE_ELEMENT • CLOUD | It is one of the following values: |  |  |

---

## Device Information

This section contains 27 field(s) related to device information.

| Field | Type | Required | Description | Format | Example | Values |
|-------|------|----------|-------------|--------|---------|--------|
| `postalCode` | number | Optional | The postal code associated with the address. and hyphens (-) are allowed; max length 10 characters. | String; alphanumeric, valid for the country; whitespace |  |  |
| `walletProviderDeviceScore` | string |  | The wallet provider device score. Score value is between1 and 5, indicating the confidence level of the device, where5 indicates the most confidence. | String; max length 2 characters. | 5 |  |
| `deviceBluetoothMac` | string |  | MAC address for Bluetooth. | String; max length 24 characters. |  |  |
| `deviceIMEI` | string |  | Hardware ID of the device. | String; max length 24 characters. |  |  |
| `deviceSerialNumber` | number |  | Serial number of the mobile device. | String; max length 24 characters. |  |  |
| `deviceTimeZone` | datetime |  | Time-zone abbreviation. | String; max length 5 characters. | PDT |  |
| `deviceTimeZoneSetting` | datetime |  | Device time-zone setting. • NETWORK_SET • CONSUMER_SET | It is one of the following values: |  |  |
| `osID` | string |  | OS ID to allow building velocity and risk rules. | String; max length 24 characters. |  |  |
| `deviceLostMode` | number |  | Number of days. Values are up to 9999 number of days. | String; max length 4 characters. | 9999 |  |
| `deviceCountry` | datetime |  | Country of device at time of provisioning. | String; ISO 3166-1, alpha-2; max length 2 characters. | US |  |
| `deviceID` | number |  | For Secure Element (SE) wallet providers, this value will be the SE ID in hex binary characters transformed to a 48-character string. For Host Card Emulation (HCE) wallet providers, this field will be the Device ID as determined by the digital wallet provider (DWP). All alphanumeric and special characters are allowed for HCE DWPs. Secure Element (SE) ID represents the device ID. • For SE DWPs, this value will be the SE ID in hex binary characters transformed to a 48-character string. • For CBP DWPs, this field will be the device ID as determined by the DWP. All alphanumeric and special characters are allowed for CBP DWPs. For Card-on-File (COF) wallets, this value will not be present. For the initial Check Eligibility request on PAN enrollment, this value may not be available, however Visa will send this value if it is available. | String; max length 48 characters. |  |  |
| `deviceLanguageCode` | object |  | This value is any ISO 639 Version 3 Language Code, for example, eng (English). This language code will be used by the issuer and Visa to retrieve the Terms and Conditions (T&C). If T&Cs are not found for the Language Code in the request, the T&Cs will return the default :anguage Code of eng (English). characters. Visa Token Service - Issuer API Specifications (JSON) Encrypted Payload Data Structures 27 March 2025 Visa Confidential 67 | String; ISO-639 Version 3 Language Code, max length 3 |  |  |
| `deviceType` | string |  | Device type. Note: The deviceType field corresponds to Field 125, Usage 2 - Dataset ID 01 - Token Device, which is described in the VisaNet Authorization-Only Online Messages - Technical Specifications. • UNKNOWN • MOBILE_PHONE, which is equivalent to value 01 in Field 125 • TABLET, which is equivalent to value 02 in Field 125 • WATCH • MOBILEPHONE_OR_TABLET, which is equivalent to value 04 in Field 125 • PC • HOUSEHOLD_DEVICE • WEARABLE_DEVICE • AUTOMOBILE_DEVICE | It is one of the following values: |  |  |
| `deviceNumber` | number |  | Device number. | String; max length 13 characters. |  |  |
| `osType` | string |  | Type of operating system. • ANDROID • IOS • WINDOWS • BLACKBERRY • TIZEN • OTHER | It is one of the following values: |  |  |
| `osVersion` | object |  | Version of the operating system running on the device. Visa Token Service - Issuer API Specifications (JSON) Encrypted Payload Data Structures 27 March 2025 Visa Confidential 68 | String; max length 32 characters. | 4.4.4 |  |
| `osBuildID` | string |  | Operating system build identifier. | String; max length 32 characters. | KTU84M |  |
| `deviceIDType` | string |  | Attribute indicating the source of the Device ID value. SecureElement, TEE, or Derived | String; max length 32 characters. | The source for Device ID (deviceID) could be |  |
| `deviceManufacturer` | string |  | Manufacturer of the device. | String; max length 32 characters. | Samsung |  |
| `deviceBrand` | string |  | Brand name of the device. | String; max length 32 characters. | Galaxy |  |
| `deviceModel` | string |  | model of the device. | String; max length 32 characters. | SGH-T999 |  |
| `deviceLocation` | number |  | Obfuscated geographic location of the device. Initially, when provisioned, this contains the general location of the device. Information will be supplied with latitude/longitude rounded to the nearest whole digit. | String; max length 25 characters. | +37/-121 |  |
| `deviceIndex` | number |  | The index number from Visa where the deviceID is stored. This is required for token device binding. | Integer; max length 2 digits. |  |  |
| `deviceIPAddressV4` | number | Optional | The IP address of the device at the time of the provisioning request, with the value represented in 255.255.255.255 format. An octet (255) may be 1-3 digits in length but cannot contain any leading zeros. | String; max length 15 characters. |  |  |
| `locationSource` | object |  | Source used to identify consumer location. • WIFI • CELLULAR • GPS • OTHER Visa Token Service - Issuer API Specifications (JSON) Encrypted Payload Data Structures 27 March 2025 Visa Confidential 69 | It is one of the following values: |  |  |
| `originalDeviceID` | enum |  | Device ID from the original provision. This field is populated only when performing token-for-token provisioning and can be used only in the following APIs: | String; max length 48 characters. |  | `Approve Provisioning`, `Approve Provisioning Stand-In Notification`, `Token Create Notification` |
| `originalDeviceType` | string |  | Device type from the original provision. This field is populated only when performing token-for-token provisioning and can be used only in the following APIs: Visa Token Service - Issuer API Specifications (JSON) Encrypted Payload Data Structures 27 March 2025 Visa Confidential 70 | It is one of the following values: |  | 12 options: `Approve Provisioning`, `Approve Provisioning Stand-In Notification`... |

---

## Risk Information

This section contains 6 field(s) related to risk information.

| Field | Type | Required | Description | Format | Example | Values |
|-------|------|----------|-------------|--------|---------|--------|
| `riskAssessmentScore` | string | Optional | Advanced Authorization (AA) Risk Score is generated by VisaNet on the last payment transaction for the PAN. Values are 0 through 99, with a higher value indicating higher risk. This value is calculated by the AA Risk engine, based on the PAN’s transaction pattern (long-term and short-term). If available, it will be provided in Check Eligibility. | String; max length 2 characters. |  |  |
| `walletProviderRiskAssessment` | string |  | Wallet provider risk assessment. If the DWP sends the value, Visa will send it to the issuer. • 0-- Unconditionally approved. • 1-- Conditionally approved with further consumer verification. • 2-- Not approved | It is one of the following values: |  |  |
| `walletProviderRiskAssessment` | object |  | Version If the DWP sends this information, Visa will send it to the issuer. May contain separators to indicate major and minor components, for example, periods, hyphens, slashes, and other similar characters. Visa Token Service - Issuer API Specifications (JSON) Encrypted Payload Data Structures 27 March 2025 Visa Confidential 62 | String; max length 10 characters. |  |  |
| `walletProviderPhoneScore` | number |  | The wallet provider phone score. Score value is between1 and 5, indicating the confidence level of the phone number, where5 indicates the most confidence. | String; max length 2 characters. | 5 |  |
| `walletProviderReasonCodes` | string |  | Wallet provider reason codes, in a comma-separated format. | String; max length 100 characters. |  |  |
| `riskAssessmentScore` | string |  | Values are 0 through 99. A higher value indicates a higher risk. This is calculated by the AA Risk Engine, based on the PAN’s transaction pattern (long term and short term). | String; max length 2 characters. |  |  |

---

## Address

This section contains 5 field(s) related to address.

| Field | Type | Required | Description | Format | Example | Values |
|-------|------|----------|-------------|--------|---------|--------|
| `billingAddress` | string | Conditional | Billing address associated with the payment instrument. It is required for Secure Remote Commerce. | An Address structure. |  |  |
| `Address` | string |  | This structure is used by several APIs. |  |  |  |
| `city` | number | Optional | City associated with the address. (.), single quote (‘), asterisk (*), and hyphens (-) are allowed; max length 32 characters. | String; alphanumeric; UTF-8, white space, carat (^), period |  |  |
| `state` | string | Optional | State or province code associated with the address. | String; ISO 3166-2; max length 2 characters. | NY |  |
| `country` | string | Optional | Code for a country; default is US. | String; ISO 3166-1 alpha-2; max length 2 characters. | US |  |

---

## Other Fields

This section contains 12 field(s) related to other fields.

| Field | Type | Required | Description | Format | Example | Values |
|-------|------|----------|-------------|--------|---------|--------|
| `Structures` | string |  |  |  |  |  |
| `expirationDate` | enum | Conditional | The expiration date of the payment instrument. This is a required field for Secure Remote Commerce and in the following APIs: | An Expiration Date structure. |  | `Approve Provisioning`, `Token Create Notification` |
| `highValueCustomer` | boolean | Optional | If available, it will be provided in Check Eligibility. • true-- Indicates that the customer is high value. • false-- Indicates that the customer is not high value. | It is one of the following values: |  |  |
| `month` | number | Required | The month upon which the payment instrument is set to expire. | String; numeric; length 2 digits. | "month": "09" |  |
| `year` | number | Required | The year upon which the payment instrument is set to expire. Visa Token Service - Issuer API Specifications (JSON) Encrypted Payload Data Structures 27 March 2025 Visa Confidential 58 | String; numeric; length 4 digits. | "year": "2024" |  |
| `Authentication` | string |  | • 14 Card Issuer Asserted Authentication | String; max length 2 characters. |  |  |
| `Authentication` | object |  | • 14 Card Issuer Asserted Authentication Visa Token Service - Issuer API Specifications (JSON) Encrypted Payload Data Structures 27 March 2025 Visa Confidential 61 | String; max length 2 characters. |  |  |
| `autoFillIndicator` | enum | Conditional | Indicates whether the token is for an autofill use case. This is a required field in the following APIs: on-File) is for an autofill use case. • false -- Indicates that the token is not for an autofill use case. | It is one of the following values: |  | 4 options: `Approve Provisioning`, `Approve Provisioning Stand-In Notification`... |
| `simSerialNumber` | number |  | SIM serial number of the mobile device. Visa Token Service - Issuer API Specifications (JSON) Encrypted Payload Data Structures 27 March 2025 Visa Confidential 63 | String; max length 24 characters. |  |  |
| `daysSinceConsumerDataLast` | number |  | AccountChange Number of days since account settings were changed (in case of a password update). If the number of days exceeds 9999, it will stay at 9999. | String; max length 4 characters. | "9999" |  |
| `numberOfTransactionsInLast` | number |  | 12months Number of transactions on this account in the last 12 months. If the number of transaction exceeds 9999, it will stay at 9999. | String; max length 4 characters. | "9999" |  |
| `issuerSpecialConditionCodes` | object |  | Supported for issuers participating in 0100 TAR. The issuer can send values for this element in the 0100 TAR response. • If the issuer sends a value in the 0100 TAR, it will be sent in this element of the Get CVM. • If no value is sent in 0100 TAR or if the issuer does not participate in TAR, this element will not be present. Visa Token Service - Issuer API Specifications (JSON) Encrypted Payload Data Structures 27 March 2025 Visa Confidential 66 | String; max length 100 characters. |  |  |

---

## Field Statistics

- **Total Fields**: 89
- **Required Fields**: 4
- **Optional Fields**: 15
- **Conditional Fields**: 12

*Generated by ULTIMATE PDF Extractor - Optimized for LLM consumption*