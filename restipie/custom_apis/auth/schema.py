signup_schema = {
	"$schema":"http://json-schema.org/draft-07/schema#",
	"title":"Sign up",
	"type" : "object",
	"properties" : {
		"fullname" : {
			"type" : "string",
			"minLength": 2,
			"maxLength": 64
		},
		"mobile_no": { "type" : "string", "pattern": "^[0-9]{11}$" },
		"email": { "type" : "string", "format": "email" },
		"location": {
			"type" : "string",
			"minLength": 5,
			"maxLength": 150
		}
	},
	"required": ["fullname", "mobile_no", "email"]
}
