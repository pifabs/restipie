user_schema = {
	"$schema":"http://json-schema.org/draft-07/schema#",
	"title":"Test User",
	"type" : "object",
	"properties" : {
		"email" : {
			"type" : "string",
			"format": "email",
			"description": "Email of the user"
			},
		"fullname" : {"type" : "string"},
		"age": {"type" : "integer", "minimum": 18}
	},
	"required": ["email", "fullname"]
}