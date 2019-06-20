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