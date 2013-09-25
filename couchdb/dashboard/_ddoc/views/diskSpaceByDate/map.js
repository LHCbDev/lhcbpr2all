function(doc) {
	if (doc.type == 'disk-usage'){
		var key = doc.updated;
		var dateTemp = new Date(eval(key.substring(0,4)),eval(key.substring(5,7))-1,eval(key.substring(8,10)),eval(key.substring(11,13)),eval(key.substring(14,16)),eval(key.substring(17,19)));
		var data = {path:doc.path,slot : doc.slot, build_id:doc.build_id ,blocks:doc.blocks,bavail:doc.bavail,bsize:doc.bsize,date:dateTemp.toGMTString()};
		emit(key,data);
	}
}