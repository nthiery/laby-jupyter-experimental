
(*
 * Copyright (C) 2007-2014 The laby team
 * You have permission to copy, modify, and redistribute under the
 * terms of the GPL-3.0. For full license terms, see gpl-3.0.txt.
 *)

val conf : Conf.ut
val conf_tilesize : int Conf.t
val conf_source_style : string Conf.t
val conf_playback_rate : float Conf.t
val conf_cue_rate : float Conf.t

exception Error of F.t

val run_gtk : unit -> unit
