const SCREENWIDTH = document.documentElement.clientWidth;
const WEEKDAYS = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];

function format(str) {
    if(arguments.length > 1) {
            const t = typeof arguments[1];
            const args = (t === 'string' || t === 'number')
                    ? Array.prototype.slice.call(arguments, 1)
                    : arguments[1];

            for(const key in args) {
                    str = str.replace(new RegExp('\\{' + key + '\\}', 'gi'), args[key]);
            }
    }
    return str;
}

function unique(array){
    return array.filter(function(value, index, self) { 
        return self.indexOf(value) === index;
    });
}

function clear(elem){
    while (elem.firstChild){
        elem.removeChild(elem.firstChild);
    };
}
function hideInputs(elem){
    array(elem.childNodes).forEach(function(input, i, arr){
        if (input.type != "hidden") {input.type = "hidden"};
    });
}


function array(arrayLikeObj){
    return Array.prototype.slice.call(arrayLikeObj);
}

function stripTimeZeroes(timeStr){
    if (timeStr.charAt(0) == 0){
        return timeStr.substring(1, timeStr.length);
    };  return timeStr;
}
function stripAmPm(timeStr){
    return timeStr.toLowerCase().replace('pm', '').replace('am', '').trim();
}

// From SO
Date.prototype.dateString = function() {
  var m = this.getMonth() + 1;
  var d = this.getDate();
  return [(m>9 ? '' : '0') + m,
          (d>9 ? '' : '0') + d,
          this.getFullYear()].join('/');
};
Date.prototype.addDays = function(days) {
    var date = new Date(this.valueOf());
    date.setDate(date.getDate() + days);
    return date;
}

// From SO
function isDescendant(parent, child) {
     var node = child.parentNode;
     while (node != null) {
         if (node == parent) {
             return true;
         }
         node = node.parentNode;
     }
     return false;
}


// From MDN, modified slightly to be more robust
function makeDraggable(elmnt, ...andSelectors) {
  var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
  elmnt.andSelectors = andSelectors;

  elmnt.onmousedown = dragMouseDown;

  function dragMouseDown(e) {
    e = e || window.event;
    if (e.target == this || array(this.querySelectorAll(this.andSelectors.join(','))).includes(e.target)) {
        e.preventDefault();
        // get the mouse cursor position at startup:
        pos3 = e.clientX;
        pos4 = e.clientY;
        document.onmouseup = closeDragElement;
        // call a function whenever the cursor moves:
        document.onmousemove = elementDrag;
    }
  }

  function elementDrag(e) {
    e = e || window.event;
    e.preventDefault();
    // calculate the new cursor position:
    pos1 = pos3 - e.clientX;
    pos2 = pos4 - e.clientY;
    pos3 = e.clientX;
    pos4 = e.clientY;
    // set the element's new position:
    elmnt.style.top = (elmnt.offsetTop - pos2) + "px";
    elmnt.style.left = (elmnt.offsetLeft - pos1) + "px";
  }

  function closeDragElement() {
    // stop moving when mouse button is released:
    document.onmouseup = null;
    document.onmousemove = null;
  }
}