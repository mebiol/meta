const OpenAI=require("openai");
const openai=new OpenAI();
const fs = require('fs');
let db={};
let readUser=async()=>{
	try {
		fs.readFile('./user.txt',(err, data)=>{
			if (err){
				console.log(err);
			}else{
				let txt='{'+data.toString().slice(0,-2)+'}';
				db=JSON.parse(txt);
				console.log(db);
			}
		});
	} catch (err) {a
		console.log(err);
	}
}
readUser();
let wait=(s)=>{return new Promise(r=>setTimeout(()=>{r()},s*1000))};
let assistants=async(user,msg)=>{
	let answer='Please ask again.';
	if (user&&msg){
		try{
			let assistant_id="asst_wpegT5qk3IecHfYgAb31PIQh";
			let thread_id=db[user];
			if (!thread_id){
				let thread = await openai.beta.threads.create();
				thread_id=thread.id;
				db[user]=thread_id;
	//			let write=await fs.appendFile('./user.txt','"'+user+'":"'+thread_id+'",\n');
				fs.appendFile('./user.txt','"'+user+'":"'+thread_id+'",\n',(err)=>{
					if (err){
						console.log(err);
					}else{
						console.log(new Date(),thread_id,[user],'new_user');				
					}
				});
			}
//			console.log(db);		
			let message = await openai.beta.threads.messages.create(
			  thread_id,
			  {
				role: "user",
				content: msg
			  }
			);
			let run = await openai.beta.threads.runs.create(
			  thread_id,
			  { 
				assistant_id: assistant_id,		//assistant.id,
	//			instructions: "Please address the user as Jane Doe. The user has a premium account."
			  }
			);
			let run_id=run.id;
			do {
				run = await openai.beta.threads.runs.retrieve(
				  thread_id,
				  run_id
				);
				console.log(new Date(),thread_id,run.status);
				await wait(1);
			}
			while (!['completed','expired','failed','cancelled'].includes(run.status));
			if (run.status=='completed'){
				messages = await openai.beta.threads.messages.list(
				  thread_id
				);	
				answer=messages.data[0].content[0].text.value;
//				messages.data.map(a=>console.log(a.content));
			}
		}catch(err){
			console.log(new Date(),'Err',err);
		}
	}
	return answer
}
module.exports = {
	assistants,
}

/*	
	const assistant = await openai.beta.assistants.create({
	  name: "Math Tutor",
	  instructions: "You are a personal math tutor. Write and run code to answer math questions.",
	  tools: [{ type: "code_interpreter" }],
	  model: "gpt-4-1106-preview"
	});
*/