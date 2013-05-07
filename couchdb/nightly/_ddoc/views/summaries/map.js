function(doc) {
  if (doc.type == "slot-build") {
    emit([doc.slot, doc.build_id, doc.platform],
         {"host": doc.host,
          "job_id": doc.job_id,
          "started": doc.started,
          "completed": doc.completed});
    for(var idx in doc.summary) {
      emit([doc.slot, doc.build_id, doc.platform, parseInt(idx)],
           doc.summary[idx]);
    }
  }
}
