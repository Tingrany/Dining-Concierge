(function(){
  var chat = {

  token_response:'',
  id_token:'',

  s1: function(){
    var id_token = "";
    var AWS = window.AWS;
    var parser = document.createElement('a');
    parser.href = window.location.href;

    var raw_code = parser.search;
    var target_code = raw_code.slice(6,);
    console.log(target_code);

    var token_response = "";
    console.log("Start testing the cognito");

    var settings = {
        "async": false,
        "crossDomain": true,
        "url": "https://mycchw1.auth.us-east-1.amazoncognito.com/oauth2/token",
        "method": "POST",
        "headers": {
              "content-type": "application/x-www-form-urlencoded"
        },
        "data": {
              "grant_type": "authorization_code",
              "client_id": "1o7fcmf3k6ebt9au8e15k31c7e",
              "redirect_uri": "https://s3.amazonaws.com/mycchwonev2/index.html",
              "code": target_code
        }
    }
    $.ajax(settings).done((response) => {
        this.token_response = response;
        console.log(response);
        console.log(response.id_token);
        console.log("test");
    });
  },
 

 s2 :function() {
    AWS.config.region = 'us-east-1';
    // Configure the credentials provider to use your identity pool
    var UserPoolId = 'us-east-1_H5YMyDzYC';
    var loginKey = 'cognito-idp.' + 'us-east-1' + '.amazonaws.com/' + UserPoolId;
    this.id_token = this.token_response.id_token;
    console.log("start step1: confige credentials");
    AWS.config.credentials = new AWS.CognitoIdentityCredentials({
         IdentityPoolId: 'us-east-1:29173480-f37d-4ea2-af04-f09b4b188231',
                   // IdentityId: identityId,
         Logins: {
                   'cognito-idp.us-east-1.amazonaws.com/us-east-1_H5YMyDzYC': this.id_token
         }
      });
    },
 
 s3: function() {

    AWS.config.credentials.refresh((err) => {
        if (err) {
            console.log(err);
        } else {
            console.log('logged in');
        }
      });
    },

 s4: function() {
       AWS.config.credentials.get((err) => {
          if (err) {
             console.log(err);
             return;
          }
          else{
             var accessKeyId = AWS.config.credentials.accessKeyId;
             var secretAccessKey = AWS.config.credentials.secretAccessKey;
             var sessionToken = AWS.config.credentials.sessionToken;
             AWS.config.update({
                 accessKeyId: accessKeyId,
                 secretAccessKey: secretAccessKey,
                 sessionToken: sessionToken
              })
                                  
              console.log("accessKeyId: ", accessKeyId);
              console.log("secretAccessKey: ", secretAccessKey);
              console.log("sessionToken: ", sessionToken);
           }
       });
    },
  messageToSend: '',
 
  init: function() {
      this.s1();
      this.s2();
      this.s3();
      this.s4();
      this.cacheDOM();
      this.bindEvents();
      this.render();
  },
 
  cacheDOM: function() {
      this.$chatHistory = $('.chat-history');
      this.$button = $('button');
      this.$textarea = $('#message-to-send');
      this.$chatHistoryList =  this.$chatHistory.find('ul');
  },
 
  bindEvents: function() {
      this.$button.on('click', this.addMessage.bind(this));
      this.$textarea.on('keyup', this.addMessageEnter.bind(this));
  },
 
  render: function() {
      this.scrollToBottom();
      if (this.messageToSend.trim() !== '') {
          var template = Handlebars.compile( $("#message-template").html());
      var context = {
          messageOutput: this.messageToSend,
          time: this.getCurrentTime()
      };
  console.log(this.messageToSend);
      this.$chatHistoryList.append(template(context));
      this.scrollToBottom();
 
 // connect with API Gateway
  var apigClient = apigClientFactory.newClient({
  });
  var send_token = this.id_token.substr(0,20);
  var body =
  //This is where you define the body of the request
  {
    "messages":
    [
      {
      "type": "string",
      "unstructured": {
      "id": send_token,
      "text": this.messageToSend,
      "timestamp": "string"
      }  
      }
    ]
  };
  console.log(body);
 
  var templateResponse = Handlebars.compile( $("#message-response-template").html());
  apigClient.chatbotPost({}, body, {})
  .then((ans) => {
       console.log(ans);
       console.log(ans.data);
       //This is where you would put a success callback
       
       var contextResponse = {
          response: ans.data,
          time: this.getCurrentTime()
       };

       setTimeout(function(){
            this.$chatHistoryList.append(templateResponse(contextResponse));
            this.scrollToBottom();
        }.bind(this), 1500);

  }).catch(function(ans){
       //This is where you would put an error callback
  });
  this.$textarea.val('');
 
    }
 },
 
  addMessage: function() {
      this.messageToSend = this.$textarea.val();
      this.render();
  },
  addMessageEnter: function(event) {
 // enter was pressed
  if (event.keyCode === 13) {
      this.addMessage();
      }
  },
  scrollToBottom: function() {
      this.$chatHistory.scrollTop(this.$chatHistory[0].scrollHeight);
  },
  getCurrentTime: function() {
      return new Date().toLocaleTimeString().
          replace(/([\d]+:[\d]{2})(:[\d]{2})(.*)/, "$1$3");
  },
  getRandomItem: function(arr) {
      return arr[Math.floor(Math.random()*arr.length)];
  }
 };
 
 chat.init();
 
 var searchFilter = {
    options: { valueNames: ['name'] },
    init: function() {
        var userList = new List('people-list', this.options);
        var noItems = $('<li id="no-items-found">No items found</li>');
        userList.on('updated', function(list) {
             if (list.matchingItems.length === 0) {
                    $(list.list).append(noItems);
             } else {
                    noItems.detach();
             }
        });
    }
 };
 
 searchFilter.init();
 
 })();