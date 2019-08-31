// Courtesy of Alwinfy

const fileify = (form, cb) => {
  const die = str => {throw new Error(str)};
  if(!form instanceof HTMLFormElement)
    die("pls fileify a form");
  form.addEventListener("submit", ev => {
    // sad face debug
    ev.preventDefault();

    var files = form.querySelectorAll("input[type=file]");
    let count = files.length;
    console.log(`fileify ${form} count ${count}`);

    files.forEach(inp => {
      if(!inp.name) die("file input need name");
      if (inp.files.length < 1) { (cb || form.submit)(); return false };
      const file = inp.files[0];
      const filedata = document.createElement("input");
      filedata.type = "hidden";
      filedata.name = "_" + inp.name;
      console.log(inp.name, file.name, inp.value, file.value, inp, file, inp.files)
      //inp.value = file.name;
      const reader = new FileReader();
      reader.addEventListener("loadend", () => {
        filedata.value = encodeURI(reader.result);
        form.appendChild(filedata);
        if(!--count){
          (cb || form.submit)();
        };
      });
      reader.readAsBinaryString(file);
    });

    return false;
  });
};

/*
// client code
const form = document.querySelector('form'); // change to suit needs
fileify(form);
*/
