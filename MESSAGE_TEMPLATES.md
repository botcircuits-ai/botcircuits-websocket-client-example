## Type : TEXT
### Example payload
```json
{
  "type": "TEXT",
  "content": "Hello !!!"
}
```

## Type : BUTTONS
### Example payload
```json
{
  "type": "BUTTONS",
  "content": {
      "displayText": "Select your card type to proceed payment",
      "optionsTitle": "Please select card type",
      "buttons": [
        {
          "actionType": "set_value",
          "slot": "cardType",
          "title": "Visa",
          "payload": "visa"
        },
        {
          "actionType": "set_value",
          "slot": "cardType",
          "title": "Master",
          "payload": "master"
        }
      ]
    }
}
```

## Type : IMAGE
### Example payload
```json
{
  "type": "IMAGE",
  "content": {
    "url": "<image url>",
    "caption": "Image caption"
  }
}
```

## Type : CARDS
### Example payload
```json
{
  "type": "CARDS",
  "content": {
    "displayText": "How can I help you?",
    "cards": [
      {
        "title": "Loan Inquiries",
        "image": "<image url>",
        "buttons": [
          {
            "actionType": "set_value",
            "slot": "loan_inq",
            "title": "Eligibility",
            "payload": "eligi"
          },
          {
            "actionType": "set_value",
            "slot": "loan_inq",
            "title": "Documents Required",
            "payload": "docs"
          },
          {
            "actionType": "set_value",
            "slot": "loan_inq",
            "title": "More Info",
            "payload": "more"
          }
        ]
      }
    ]
  }
}
```
