/**
 * Additional methods to the String class
 */

String.prototype.between = function(a, b) {
    var result = null;
    var indexA = this.indexOf(a);
    if(indexA != -1){
        var indexB = this.indexOf(b, indexA);
        if(indexB != -1 && indexB > indexA)
            result = this.substring(indexA + 1, indexB);
    }
    return result;
}
